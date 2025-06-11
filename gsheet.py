import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import GS_CREDENTIALS, GS_SPREADSHEET_ID, GS_URL_TEMPLATE, GS_WORKSHEET_NAME


def get_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        GS_CREDENTIALS, scope
    )
    gc = gspread.authorize(credentials)

    sh = gc.open_by_key(GS_SPREADSHEET_ID)

    try:
        worksheet = sh.worksheet(GS_WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        worksheet = sh.add_worksheet(title=GS_WORKSHEET_NAME, rows="100", cols="20")

    return worksheet


def init_sheet():
    worksheet = get_sheet()
    headers = [
        "User ID", "Sapboard ID", "Sapboard Name",
        "Admin ID", "Admin Name",
        "Start Time", "End Time", "Duration (h)", "Cost (RUB)"
    ]
    if worksheet.row_values(1) != headers:
        worksheet.insert_row(headers, index=1)


def add_rental_to_sheet(
        user_id, sapboard_id, sapboard_name, admin_id, admin_name, start_time, end_time, duration, cost
    ):
    worksheet = get_sheet()
    row = [
        user_id,
        sapboard_id,
        sapboard_name,
        admin_id,
        admin_name,
        start_time.strftime("%Y-%m-%d %H:%M:%S"),
        end_time.strftime("%Y-%m-%d %H:%M:%S") if end_time else "-",
        f"{duration:.2f}",
        f"{cost:.2f}"
    ]
    worksheet.append_row(row)


def get_sheet_url():
    worksheet = get_sheet()
    sheet_id = worksheet.spreadsheet.id
    return GS_URL_TEMPLATE.format(sheet_id=sheet_id)
