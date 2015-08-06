import ply.lex as lex
import ply.yacc as yacc
import re, pprint, os

class Parser:
    """
    Base class for a lexer/parser that has the rules defined as methods
    """
    tokens = ()
    precedence = ()

    def __init__(self, filename, **kw):
        self.filename = filename
        self.debug = kw.get('debug', 0)
        self.names = { }
        try:
            modname = os.path.split(os.path.splitext(__file__)[0])[1] + "_" + self.__class__.__name__
        except:
            modname = "parser"+"_"+self.__class__.__name__
        self.debugfile = modname + ".dbg"
        self.tabmodule = modname + "_" + "parsetab"
        #print self.debugfile, self.tabmodule

        # Build the lexer and parser
        self.lexer = lex.lex(module=self, debug=self.debug)
        self.parser = yacc.yacc(module=self,
                  debug=self.debug,
                  debugfile=self.debugfile,
                  tabmodule=self.tabmodule)

    def run(self):
        self.run_on_file(self.filename)

    def run_on_file(self,filename):
        data = ''
        with open(filename) as f:
            for line in f:
                data += line

        #lexer debugging
        if 0:
            self.lexer.input(data)

            tok = self.lexer.token()
            while tok:
                print tok
                tok = self.lexer.token()

        self.parser.parse(data)

        #while 1:
            #try:
                #self.parser.parse(data)
            #except TypeError as e:
                #print e
                #break


class TclParser(Parser):

    tokens = (
            'COMMENT',
            'WHITESPACE',
            'NEWLINE',
            'SEMICOLON',
            'BACKSLASH',
            'LBRACKET',
            'QUOT',
            'RPAREN',
            'RBRACKET',
            'LBRACE',
            'RBRACE',
            'TEXT',
        )

    t_WHITESPACE = r'[ \t]+'
    t_SEMICOLON = r';'
    t_BACKSLASH = r'\\'
    t_LBRACKET = r'\['
    t_QUOT = r'"'
    t_RPAREN = r'\)'
    t_RBRACKET = r'\]'
    t_LBRACE = r'\{'
    t_RBRACE = r'\}'
    t_TEXT = r'[\w\d\-\/\.\$\!\=]'

    def __init__(self,filename,**kw):
        Parser.__init__(self,filename,**kw)
        self.pp = pprint.PrettyPrinter()
        self.variables = {}


    def t_COMMENT(self,t):
        r'\#.*\n?'
        if '\n' in t.value:
            t.lexer.lineno += 1
        pass

    # Error handling rule
    def t_error(self,t):
        print "Illegal character '%s'" % t.value[0]
        t.lexer.skip(1)

    def t_NEWLINE(self,t):
        r'\n'
        t.lexer.lineno += 1
        return t

    def p_end(self,p):
        '''end : script
               | empty'''
        self.pp.pprint(self.variables)

    def p_script(self,p):
        '''script : command
                  | script script'''
        if len(p) == 3:
            p[0] = p[1] + p[2]
        else:
            p[0] = [p[1]]

    def p_commandend(self,p):
        '''commandend : NEWLINE
                      | SEMICOLON'''
        p[0] = p[1]

    def p_empty_command(self,p):
        '''command : commandend'''
        p[0] = []

    def p_string_text(self,p):
        '''string : TEXT
                  | string TEXT
                  | string string'''
        if len(p) == 3:
            p[0] = p[1] + p[2]
        else:
            p[0] = p[1]

    def p_longwhitespace(self,p):
        '''longwhite : BACKSLASH NEWLINE'''
        p[0] = ' '

    def p_longwhitespace_cont(self,p):
        '''longwhite : longwhite WHITESPACE'''
        p[0] = p[1]

    def p_backslash(self,p):
        '''string : BACKSLASH TEXT
                  | BACKSLASH LBRACKET'''
        p[0] = p[2]

    def p_subcommand(self,p):
        '''subcommand : LBRACKET
                      | subcommand word'''
        if len(p) == 2:
            p[0] = []
        else:
            p[0] = p[1] + [p[2]]

    def p_command_subcommand(self,p):
        '''string : subcommand RBRACKET'''
        p[0] = self.interpret(p,1)

    def p_quotword_start(self,p):
        '''quotword : QUOT'''
        p[0] = ''

    def p_quotword_cont(self,p):
        '''quotword : quotword TEXT
                    | quotword commandend
                    | quotword LBRACKET
                    | quotword WHITESPACE
                    | quotword RBRACKET
                    | quotword LBRACE
                    | quotword RBRACE'''
        p[0] = p[1] + p[2]

    def p_quotword_end(self,p):
        '''word : quotword QUOT'''
        p[0] = p[1]

    def p_braceword_start(self,p):
        '''braceword : LBRACE'''
        p[0] = p[1]

    def p_braceword_cont(self,p):
        '''braceword : braceword TEXT
                     | braceword commandend
                     | braceword WHITESPACE
                     | braceword longwhite
                     | braceword word'''
        p[0] = p[1] + p[2]

    def p_braceword_end(self,p):
        '''word : braceword RBRACE'''
        p[0] = p[1] + p[2]

    def p_command_word(self,p):
        '''command : wordlist commandend'''
        p[0] = p[1]
        self.interpret(p,0)

    def p_word_list(self,p):
        '''wordlist : word
                    | wordlist word'''
        if len(p) == 3:
            p[0] = p[1] + [p[2]]
        else:
            p[0] = [p[1]]

    def p_word_string(self,p):
        '''word : string
                | braceword
                | string WHITESPACE
                | string longwhite
                | word WHITESPACE
                | word longwhite'''
        p[0] = p[1]


    def p_empty(self,p):
        'empty : '
        pass

    def p_error(self,p):
        if p:
            #print("Syntax error at token", p.type)
            # Just discard the token and tell the parser it's okay.
            #self.parser.errok()
            raise TypeError("Syntax error at token %s at position %d" % (p.type,p.lexpos))
        else:
            print("Syntax error at EOF")

    def interpret(self,p,commandpos):
        command = p[commandpos]
        print command
        variable_re = re.compile(r'\$\{?(\w+)\}?')
        for pos,word in enumerate(command):
            try:
                m = variable_re.match(word)
            except TypeError:
                pass
            if m:
                print m.group(1)
                try:
                    command[pos] = self.variables[m.group(1)]
                except KeyError:
                    raise Exception("You have to define variable %s first" % (word[1:]))
                    #print "You have to define variable %s first" % (m.group(1))

        if command[0] == 'set':
            assert(len(command) == 3)
            self.variables[command[1]] = command[2]
            self.pp.pprint(self.variables)
        elif command[0] == 'getenv':
            assert(len(command) == 2)
            return os.environ[command[1]]
        elif command[0] == 'list':
            assert(len(command[1:]) > 0)
            ret_list = []
            for word in command[1:]:
                ret_list.append(word)
            return ret_list
        elif command[0] == 'source':
            assert(len(command) == 2)
            self.run_on_file(command[1])




