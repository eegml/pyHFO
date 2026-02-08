"""Development launcher — delegates to the installed entry point."""
# also used for py2app which requires a python script to build
from pyhfo2app.app import main

if __name__ == '__main__':
    main()
