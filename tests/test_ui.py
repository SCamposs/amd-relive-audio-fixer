import unittest
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from mediafix.window import Window

class InterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
    def test_dropdowns_and_queue(self):
        window = Window()
        window.show()
        window.activateWindow()
        QTest.qWaitForWindowExposed(window)
        QTest.qWait(150)
        self.app.processEvents()
        window.mode.setFocus()
        QTest.keyClick(window.mode, Qt.Key.Key_Down)
        self.assertEqual(window.mode.currentIndex(), 1)
        window.mode.showPopup()
        self.app.processEvents()
        self.assertTrue(window.mode.view().isVisible())
        window.mode.hidePopup()
        window.mode.setCurrentIndex(2)
        self.assertTrue(window.audio_format.isEnabled())
        window.add_files([__file__, __file__])
        self.assertEqual(window.table.rowCount(), 1)
        window.table.selectRow(0)
        window.remove_files()
        self.assertEqual(window.table.rowCount(), 0)
        window.close()
