def test_version():
    import pyhfo2app

    assert pyhfo2app.__version__ == "1.0.0"


def test_entry_point():
    from pyhfo2app.app import main

    assert callable(main)


def test_core_imports():
    from pyhfo2app.hfo_app import HFO_App
    from pyhfo2app.hfo_feature import HFO_Feature
    from pyhfo2app.classifer import Classifier
