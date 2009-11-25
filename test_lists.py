import lazyjson
import jsonlib2

simple = '["asfdf",2343, 4.5, "asdfasdf","adf" ,"asdsdsa"]'

def test_parse():
    x = lazyjson.loads(simple)
    assert x
    
def test_access():
    x = lazyjson.loads(simple)
    assert x[0] == 'asfdf'
    assert x[3] == 'asdfasdf'
    assert x[1] == 2343
    assert x[2] == 4.5
    assert x[4] == 'adf'
    assert x[5] == 'asdsdsa'
    
def test_serialize_unchanged():
    x = lazyjson.loads(simple)
    assert lazyjson.dumps(x) == simple    

def test_serialize_changed():
    x = lazyjson.loads(simple)
    x[0] ; x[1] ; x[2] ; x[3]
    y = lazyjson.dumps(x)
    assert y == simple
    
if __name__ == "__main__":
    test_parse()
    test_access()
    test_serialize_unchanged()
    test_serialize_changed()

