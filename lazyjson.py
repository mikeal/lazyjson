from StringIO import StringIO

try:
    import httplib2 as json
except:
    try:
        import simplejson as json
    except:
        import json

parser_function = json.loads
numbers = set(('0','1','2','3','4','5','6','7','8','9',))

def scan_to_next(s, index, ignore=[' ']):
    while s[index] not in ignore:
        index += 1
    return s[index], index
    
def find_not_escaped(string, sub, index, escape='\\'):
    index = string.find(sub, index)
    if index is -1:
        return index
    while string[string.find(sub, index) - 1] is not escape:
        index = (string.find(sub, index) + 1)
    return index

class Parser(object):
    def __init__(self, stream, readsize=1024, parser_function=parser_function):
        self.stream = stream
        self.readsize = readsize
        self.buffer = ""
        self.decoded_chunks = {}
    def read_chunk(self):
        block = self.stream.read(self.readsize)
        self.buffer += block
        return block

class LazyDict(dict):
    def __init__(self, parser, start_index):
        self.parser = parser
        self.start_index = start_index

class LazyList(list):
    def __init__(self, parser, start_index, end_index=None):
        self.parser = parser
        self.start_index = start_index
        self.current_index = start_index
        self.end_index = end_index
        self.additional_items = []
        self.index_buffer_map = {}
    def _find_next_item(self):
        if self.parser.buffer[self.current_index] == ']':
            raise IndexError("Already read to end of array")
        # Attempt to insure , or ] in the current block
        while ( find_not_escaped(self.parser.buffer, ',', self.current_index) is -1 ) and ( 
                find_not_escaped(self.parser.buffer, ']', self.current_index) is -1 ):
            if not self.parser.read_chunk():
                raise Exception("FAIL!")
        s, start_index = scan_to_next(self.parser.buffer, self.current_index)
        end_index = find_not_escaped(self.parser.buffer, s, start_index + 1)
        
        obj = type_map[s](self.parser,start_index,end_index) 
        self.parser[(start_index, end_index,)] = obj
        return obj
        
    def _set_next(self):
        obj, start, end = self._find_next_item()
        list.append(self, obj)
        self.index_buffer_map[list.__len__(self) - 1] = (start, end,)
            
    def __getitem__(self, i):
        if list.__len__(self) >= (i + 1):
            return list.__getitem__(self, i)
        else:
            while list.__len__(self) < (i + 1): 
                self._set_next()
            return list.__getitem__(self, i)
    
    def __setitem__(self, i, value):    
        while list.__len__(self) < (i + 1): 
            self._set_next()
        list.__setitem__(self, i, value)
        self.parser.decoded_chunks[self.index_buffer_map[i]] = value
    
    def append(self, value):
        list.append(self, value)
        self.additional_items.append(value)
        

def parse_string(p, s, e):
    return json.loads(p.buffer[s:e+1])
def parse_dict(b, s, e):
    return LazyDict(b, s, e)
def parse_list(b, s, e):
    return LazyList(b, s, e)

type_map = {'"':parse_string, '{':parse_dict, '[':parse_list}        

def loads(stream, readsize=1024, parser_function=None, decoder_function=None):
    if not hasattr(stream, 'read'):
        stream = StringIO(stream)
        readsize = stream.len
    parser = Parser(stream, readsize)
    parser.read_chunk()
    