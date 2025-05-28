from PyQt5.QtWidgets import QApplication
import sys
from pet.desktop_pet import DesktopPet

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pet = DesktopPet()
    pet.show()
    sys.exit(app.exec_())