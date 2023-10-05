from PyQt5.QtWidgets import (
    QDialog, QMainWindow, QFileDialog, QProgressBar, QErrorMessage
)

def assert_conditions(qt, conditions):
    keep = 1
    text_list = []
    for condition in conditions:
        if condition.text() == "":
            keep = 0
        else:
            text_list.append(condition.text())
    if not keep:
        title = 'Warning'
        message = f'Missing input: {condition.objectName}'
        qt.pop_message(title, message)

    else:
        return text_list

