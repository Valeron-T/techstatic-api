import json
from io import BytesIO

import requests
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageDraw, ImageFont
from urllib.request import urlopen  # Import for downloading the font
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from pydantic import BaseModel
import qrcode
import uvicorn
import os
import hypercorn

app = FastAPI()

# app.mount("/", StaticFiles(directory="static"), name="static")

# cred = open(rf'{os.getcwd()}\creds.json')
# cred_dict = json.load(cred)
# print(os.environ.get('CREDS'))
cred_dict = json.loads(os.environ.get('CREDS'))

credentials = ServiceAccountCredentials.from_json_keyfile_dict(cred_dict,
                                                               scopes=["https://www.googleapis.com/auth/drive"])
# forms_service = build('forms', 'v1', credentials=credentials)
drive_service = build('drive', 'v3', credentials=credentials)
sheets_service = build('sheets', 'v4', credentials=credentials)

spreadsheet_id = '1Cj44xd3LXJT2oNkJzb_MPl2Ba9zjTL5vR4c4K8R-nuA'

# Download the font from the remote URL
font_url_league = "https://valeron-t.github.io/discord-webhook-test/LeagueGothic-Regular.ttf"  # Replace with actual URL
with urlopen(font_url_league) as font_file_l:
    font_bytes_league = font_file_l.read()
    
# Download the font from the remote URL
font_url_poppins = "https://valeron-t.github.io/discord-webhook-test/Poppins-Regular.ttf"  # Replace with actual URL
with urlopen(font_url_poppins) as font_file_p:
    font_bytes_poppins = font_file_p.read()

print("error")


ticket = Image.open(requests.get(
    "https://raw.githubusercontent.com/Valeron-T/discord-webhook-test/main/tech-ticket.jpg",
    stream=True).raw)

@app.get("/")
def hello():

    return Response(json.dumps({"message": "Hello"}), 200)


@app.get("/test")
def hello():
    return Response(json.dumps({"message": "API is running"}), 200)


@app.get("/generate-qr")
def new_qr(response_id: str, name: str, venue: str, date:str):
    print(os.getcwd())
    try:
        qr = qrcode.QRCode(box_size=13)
        qr_string = response_id
        img = ticket
        qr.add_data(qr_string)
        qr.make()

        # Create a drawing object on the base image
        draw = ImageDraw.Draw(img)

        # Create a font object from the downloaded font data
        league = ImageFont.truetype(BytesIO(font_bytes_league), 130)  # Adjust font size as needed
        poppins = ImageFont.truetype(BytesIO(font_bytes_poppins), 48)  # Adjust font size as needed

        # Calculate text positions based on image dimensions and content
        _, _, text_width, text_height = draw.textbbox((0, 0), name, font=league) 
        _, _, text_width_poppins, text_height_poppins = draw.textbbox((0, 0), venue, font=poppins) 

        name_x = (img.width - text_width) / 3.5
        name_y = (img.width - text_width) / 7.5  # Adjust spacing as needed
        date_y = name_y + text_height +30  # Adjust spacing as needed
        venue_y = date_y + text_height_poppins + 20  # Adjust spacing as needed
        date_x = name_x + 0.25 * name_x
        print(name_x, name_y, venue_y, date_y, text_width, text_height)

        img_qr = qr.make_image(fill_color="black", back_color="#E6E6FA")
        pos = (1500, 70)
        img.paste(img_qr, pos)
        stream = BytesIO()
        draw.text((name_x, name_y), f"{name.upper()}", font=league, fill="white", align="center")
        draw.text((date_x-10, date_y), f"{date.upper()}", font=poppins, fill="white", align="center")
        draw.text((date_x-30, venue_y), f"{venue.upper()}", font=poppins, fill="white", align="center")
        img.save(stream, format='JPEG')

        file_metadata = {'name': f"{response_id}.jpeg", 'parents': ['1UWHUeV4-DW0d6ihMGYaxu_bnGKN1IXT8']}
        media = MediaIoBaseUpload(stream, mimetype='image/jpeg', )
        file = drive_service.files().create(body=file_metadata, media_body=media,
                                            fields='id').execute()
        # print(F'File ID: {file.get("id")}')
        return {"message": "QR Generated successfully! ", "status": 200}
    except Exception as e:
        print(e)
        return {"message": "Unexpected error occurred", "status": 503}

#
# @app.get("/generate-qr/early")
# def new_qr(response_id: str, ticket_type: str):
#     try:
#         qr = qrcode.QRCode(box_size=14)
#         qr_string = response_id
#         img = early_stag
#         if ticket_type == "Stag":
#             print("Stag")
#         elif ticket_type == "Couple":
#             img = early_couple
#         qr.add_data(qr_string)
#         qr.make()
#         img_qr = qr.make_image(fill_color="black", back_color="#E6E6FA")
#         pos = (1440, 90)
#         img.paste(img_qr, pos)
#         stream = BytesIO()
#         img.save(stream, format='JPEG')
#         file_metadata = {'name': f"{response_id}.jpeg", 'parents': ['1E-MPKuk-RNKYiBRuUQAOt5vXtRLFT4Si']}
#         media = MediaIoBaseUpload(stream, mimetype='image/jpeg', )
#         file = drive_service.files().create(body=file_metadata, media_body=media,
#                                             fields='id').execute()
#         # print(F'File ID: {file.get("id")}')
#         return {"message": "QR Generated successfully! ", "status": 200}
#     except:
#         return {"message": "Unexpected error occurred", "status": 503}


@app.get("/responses")
def getresponses(event_id: str):
    print("response start")
    # try:
    batch_get_values_by_data_filter_request_body = {
        'value_render_option': 'FORMATTED_VALUE',
        'data_filters': [
            {
                'gridRange': {
                    # 'sheetId': '1497832988',
                    'sheetId': event_id,
                },
            },
        ],
    }

    data = sheets_service.spreadsheets().values().batchGetByDataFilter(spreadsheetId=spreadsheet_id,
                                                                       body=batch_get_values_by_data_filter_request_body).execute()
    print(data['valueRanges'][0]['valueRange'])

    # ['Timestamp', 'Name', 'UID', 'Email_Address', 'Response ID', 'Attendance']
    headers = data['valueRanges'][0]['valueRange']['values'][0]

    values = data['valueRanges'][0]['valueRange']["values"]

    res = {"values": []}

    for value in values[1:]:
        value_dict = {}
        for i, value_key in enumerate(value):
            try:
                value_dict[headers[i]] = value_key
            except:
                value_dict[headers[i]] = ""
        res['values'].append(value_dict)

    return {"message": "Data Fetch Successful", "status": 200, "result": res}
    # except Exception as e:
    #     print(e)
    #     return {"message": "Invalid ID", "status": 403}

@app.get("/events/{dept}")
def get_events(dept: str):
    all_sheets = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    print(all_sheets['sheets'])

    events = []
    misc = []

    for sheet in all_sheets['sheets']:
        sheet_id = sheet['properties']['sheetId']
        sheet_title = sheet['properties']['title']
        event_json = {
            "name":sheet_title,
            "id":sheet_id
        }
        try:
            if str(sheet_title).split("-")[1].strip().casefold() == dept.casefold():
                events.append(event_json)
        except IndexError:
            misc.append(event_json)

    print(events)

    if dept.casefold() == 'misc'.casefold():
        result = misc
    else:
        result = events

    return Response(json.dumps({"message": "Data Fetched Successfully", "result": result}), 200)


@app.get("/events")
def get_events():
    all_sheets = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    print(all_sheets['sheets'])

    events = []
    for sheet in all_sheets['sheets']:
        sheet_id = sheet['properties']['sheetId']
        sheet_title = sheet['properties']['title']
        event_json = {
            "name": sheet_title,
            "id": sheet_id
        }
        events.append(event_json)

    print(events)
    return Response(json.dumps({"message": "Data Fetched Successfully", "result": events}), 200)


class ColumnData(BaseModel):
    col_name: str
    data: list


@app.put("/responses/by/col")  # TODO: get responses by col
def update_sheet_by_col(event_id: str, values: ColumnData):
    # Find desired column
    try:
        batch_get_values_by_data_filter_request_body = {
            'value_render_option': 'FORMATTED_VALUE',
            'data_filters': [
                {
                    'gridRange': {
                        # 'sheetId': '1497832988',
                        'sheetId': event_id,
                    },
                },
            ],
        }

        data = sheets_service.spreadsheets().values().batchGetByDataFilter(spreadsheetId=spreadsheet_id,
                                                                           body=batch_get_values_by_data_filter_request_body).execute()

        headers = data['valueRanges'][0]['valueRange']['values'][0]
        col_to_update_index = 0

        for x in headers:
            if x == values.col_name:
                col_to_update_index = headers.index(x)

        # col_to_update_index_letter = get_column_letter(col_to_update_index+1)
        print(col_to_update_index)

        # First column is timestamp which would never be changed, hence raise exception if index of col to update is 0
        if col_to_update_index == 0:
            raise Exception()
    except:
        return {"message": f"Error: Column not found in sheet {event_id}", "status": 403}

    # Update attendance column
    batch_update_values_by_data_filter_request_body = {
        'value_input_option': 'USER_ENTERED',
        'data': [
            {
                "dataFilter": {
                    "gridRange": {
                        "sheetId": event_id,
                        "startRowIndex": 1,
                        "startColumnIndex": col_to_update_index,
                        "endColumnIndex": col_to_update_index + 1,
                    }
                },
                "majorDimension": 'COLUMNS',
                "values": [
                    values.data
                ]
            }
        ],
    }

    request = sheets_service.spreadsheets().values().batchUpdateByDataFilter(spreadsheetId=spreadsheet_id,
                                                                             body=batch_update_values_by_data_filter_request_body).execute()

    return {"message": f"Updated sheet {event_id}", "Data received": values}
