class DataExportBusy(Exception):
    """The birth data kept changing while the file was assembled; the client may ask again."""

    code = "DATA_EXPORT_RETRY"
    status_code = 409
