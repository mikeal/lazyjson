from StringIO import StringIO

try:
    import jsonlib2 as json
except:
    try:
        import simplejson as json
    except:
        import json

parser_function = json.loads
numbers = ['0','1','2','3','4','5','6','7','8','9']

def scan_to_next(s, index):
    while s[index] == ' ':
        index += 1
    return s[index], index

control_map = {'{':'}','"':'"','[':']'}
control_map.update(dict([(x,',') for x in numbers]))

start_control = set(('{','[',))
end_control = set(('}',']',))

def scan_to_end(s, index, control=',', end_index=None):
    current_control = None
    in_string = False
    index -= 1
    x = 'fghjhvcvbnmmnbvcvbnm'
    while x != control or current_control is not None:
        index += 1
        if end_index is not None and index > end_index:
            e = IndexError("Reached end_index without finding control character.")
            e.index = index
            raise e
        x = s[index]
        
        if not in_string:
            if current_control is None:
                if x == '"':
                    in_string = True
                elif x in start_control:
                    current_control = x
            elif x in end_control and x == control_map[current_control]:
                current_control = None
        else:
            if x == '"':
                in_string = True

    return index
    
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
        self.read_chunk()
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
        self.unparsed_length = None
        self.index_buffer_map = {} # {0:(56,190,)}
        self.internal_index_map = {} # {0:'example'}
        
    def to_json(self, stream):
        encoded_blocks = sorted([(self.index_buffer_map[k], value) for k, value in 
                                  self.internal_index_map.items()])
        if self.end_index is None:
            self._set_end_index()
        if len(encoded_blocks) is not 0:
            i = self.start_index
            for (s, e,), obj in encoded_blocks:
                 #self.parser.buffer[i:s+1]
                stream.write(self.parser.buffer[i:s])
                _dumps(obj, stream)
                i = e
            stream.write(self.parser.buffer[i:self.end_index+1])
        else:
            stream.write(self.parser.buffer[self.start_index:self.end_index+1])
        
    def _find_item(self, index):
        if self.end_index is None:
            self._set_end_index()
        
        i = self.start_index
        for x in range(index):
            i = scan_to_end(self.parser.buffer, i+1, ',', self.end_index)
        
        s, start_index = scan_to_next(self.parser.buffer, i+1)
        end_index = scan_to_end(self.parser.buffer, start_index+1, 
                                control_map[self.parser.buffer[start_index]])

        obj = type_map[s](self.parser,start_index,end_index) 
        if type(obj) is str or type(obj) is unicode:
            end_index += 1
        self.index_buffer_map[index] = (start_index, end_index,)
        return obj
                
    def __getitem__(self, i):
        if i in self.internal_index_map:
            return self.internal_index_map[i]
        value = self._find_item(i)
        self.internal_index_map[i] = value
        return value
    
    def __setitem__(self, i, value):
        self[i]
        self.internal_index_map[i] = value
        self.parser.decoded_chunks[self.index_buffer_map[i]] = value
    
    def _set_end_index(self):
        i = self.start_index
        while self.end_index is None:
            try:
                self.end_index = scan_to_end(self.parser.buffer, i+1, ']')
            except IndexError, e:
                self.parser.read_chunk()
                i = e.index
        
    def __len__(self):
        if self.unparsed_length is None:
            if self.end_index is None:
                self._set_end_index()
            working = True
            i = self.start_index
            self.unparsed_length = 0
            while working:
                try: 
                    i = scan_to_end(self.parser.buffer, i+1, ',')
                    self.unparsed_length += 1
                except IndexError, e: 
                    working = False
        return self.unparsed_length + len(self.additional_items)
    
    def append(self, value):
        self.additional_items.append(value)

def parse_string(p, s, e):
    return json.loads(p.buffer[s:e+1])
def parse_dict(p, s, e=None):
    return LazyDict(p, s, e)
def parse_list(p, s, e=None):
    return LazyList(p, s, e)
def parse_integer(p, s, e):
    return json.loads(p.buffer[s:e].replace(' ',''))

type_map = {'"':parse_string, '{':parse_dict, '[':parse_list} 
type_map.update(dict([(x, parse_integer) for x in numbers]))       

def loads(stream, readsize=1024, parser_function=None, decoder_function=None):
    if not hasattr(stream, 'read'):
        stream = StringIO(stream)
        readsize = stream.len
    parser = Parser(stream, readsize)
    parser.read_chunk()
    return type_map[parser.buffer[0]](parser, 0, None)

special_types = set((LazyList, LazyDict,))

def _dumps(obj, stream):
    if type(obj) in special_types:
        obj.to_json(stream)
    else:
        stream.write(json.dumps(obj))    

def dumps(obj, stream=None):
    if stream is None:
        stream = StringIO()
    _dumps(obj, stream)
    if hasattr(stream, 'getvalue'):
        return stream.getvalue()
    