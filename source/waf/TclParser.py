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
            'COMMANDEND',
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

    def t_COMMANDEND(self,t):
        r'[;\n]'
        if t.value == '\n':
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

    def p_empty_command(self,p):
        '''command : COMMANDEND'''
        p[0] = []

    def p_string_text(self,p):
        '''string : TEXT
                  | string TEXT
                  | string string'''
        if len(p) == 3:
            p[0] = p[1] + p[2]
        else:
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
                    | quotword COMMANDEND
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
                     | braceword COMMANDEND
                     | braceword WHITESPACE
                     | braceword word'''
        p[0] = p[1] + p[2]

    def p_braceword_end(self,p):
        '''word : braceword RBRACE'''
        p[0] = p[1] + p[2]

    def p_command_word(self,p):
        '''command : wordlist COMMANDEND'''
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
                | word WHITESPACE'''
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
            m = variable_re.match(word)
            if m:
                print m.group(1)
                try:
                    command[pos] = self.variables[m.group(1)]
                except KeyError:
                    #raise Exception("You have to define variable %s first" % (word[1:]))
                    print "You have to define variable %s first" % (m.group(1))

        if command[0] == 'set':
            assert(len(command) == 3)
            self.variables[command[1]] = command[2]
            self.pp.pprint(self.variables)
        elif command[0] == 'getenv':
            assert(len(command) == 2)
            return os.environ[command[1]]
        elif command[0] == 'source':
            assert(len(command) == 2)
            self.run_on_file(command[1])



#class TclParser(Parser):

    #tokens = (
            #'COMMENT',
            #'WHITESPACE',
            #'NEWLINE',
            #'SEMICOLON',
            #'QUOT',
            #'TEXT',
            ##'LBRACE',
            ##'RBRACE',
            ##'DEREFERENCE',
            ##'BACKSLASH',
            ##'SLASH',
            #'LBRACKET',
            #'RBRACKET',
            ##'EQUALS',

            ##'NUMBER',
            ##'GREATER',
            ##'LPAREN',
            ##'RPAREN',
            ##'NUMOP',
        #)

    #t_WHITESPACE = r'[ \t]+'
    #t_SEMICOLON = r';'
    #t_QUOT = r'"'
    #t_TEXT = r'[\{\}\$-:!\'.\w]+'
    #t_LBRACKET = r'\['
    #t_RBRACKET = r'\]'

    ##t_DEREFERENCE = r'\$'
    ##t_LBRACE = r'\{'
    ##t_RBRACE = r'\}'
    ##t_BACKSLASH = r'\\'
    ##t_SLASH = r'\/'
    ##t_EQUALS = r'='

    ##t_NUMOP = r'[\*\+\-]'
    ##t_GREATER = r'>'
    ##t_LPAREN = r'\('
    ##t_RPAREN = r'\)'

    ##def t_NUMBER(self,t):
    ##    r'\d+'
    ##    t.value = int(t.value)
    ##    return t

    #def t_COMMENT(self,t):
        #r'\#.*\n?'
        #pass

    ## Error handling rule
    #def t_error(self,t):
        #print "Illegal character '%s'" % t.value[0]
        #t.lexer.skip(1)

    #def t_NEWLINE(self,t):
        #r'\n'
        #t.lexer.lineno += 1
        #return t

    #def __init__(self,filename,**kw):
        #Parser.__init__(self,filename,**kw)
        #self.commands = []
        #self.current_command = []
        #self.pp = pprint.PrettyPrinter()


    #def p_start(self,p):
        #'''start : script
                 #| empty'''
        #if p[1]:
            #self.interpret(p[1])

    #def p_script_empty(self,p):
        #'''script : NEWLINE
                  #| WHITESPACE'''
                  ##| script NEWLINE
                  ##| script WHITESPACE'''
        ##print "Hello"
        #if len(p) == 3:
            #p[0] = p[1]
        #else:
            #p[0] = []

    #def p_string_text(self,p):
        #'''string : TEXT
                  #| string string'''
        #if len(p) == 3:
            #p[0] = p[1] + p[2]
        #else:
            #p[0] = p[1]

    #def p_word_string(self,p):
        #'''word : string
                #| string WHITESPACE'''
        #p[0] = p[1]

    #def p_script_command(self,p):
        #'''
        #script : command SEMICOLON
               #| command NEWLINE'''
        #p[0] = [p[1]]

    #def p_script_script(self,p):
        #'script : script script'
        #p[0] = p[1] + p[2]

    #def p_quotword(self,p):
        #'quotword : QUOT string'
        #p[0] = p[2]

    #def p_quot_string(self,p):
        #'''quotword : quotword string
                    #| quotword NEWLINE
                    #| quotword WHITESPACE
                    #| quotword SEMICOLON'''
        #p[0] = p[1] + p[2]

    #def p_quot_word(self,p):
        #'string : quotword QUOT'
        #p[0] = p[1]


    #def p_bracket_command(self,p):
        #'brackword : LBRACKET string'
        #p[0] = p[1] + p[2]

    #def p_bcommand_word(self,p):
        #'''brackword : brackword string
                     #| brackword WHITESPACE'''
        #p[0] = p[1] + p[2]

    #def p_command_bcommand(self,p):
        #'string : brackword RBRACKET'
        #p[0] = p[1] + p[2]

    #def p_command_word(self,p):
        #'''command : word'''
        #p[0] = [p[1]]

    #def p_command_append(self,p):
        #'command : command command'
        #p[0] = p[1] + p[2]

    #def p_empty(self,p):
        #'empty : '
        #pass

    #def p_error(self,p):
        #if p:
            ##print("Syntax error at token", p.type)
            ## Just discard the token and tell the parser it's okay.
            ##self.parser.errok()
            #raise TypeError("Syntax error at token %s at position %d" % (p.type,p.lexpos))
        #else:
            #print("Syntax error at EOF")

    #def interpret(self,script):
        #variables = {}
        #for command in script:
            ##if command[0] == 'set':
                ##variables[command[1]] = self.interpret(command[2])
                ##print command
            ##if command[0] == 'source'
                ##with open(self.interpre(command[) as f:
                    ##self.parser.parse(
            #print command

        #print variables

    #def parse(self):
        #state = 'idle'
        #commands = []
        #command = []
        #commands_stack = []
        #expr = ''
        #depth = 0
        #ignore_newline = False
        #while True:
            #tok = self.token()
            #if not tok: break
            ##if tok.type == 'NEWLINE' and len(commands) == 20:
            ##    print commands
            ##    print command
            ##    break
            ##print commands
            ##print command
            ##print tok
            #if state == 'idle':
                #if tok.type == 'TEXT':
                    #state = 'command'
                    #expr += tok.value
                    #depth = 0
                    #command = []
            #elif state == 'command':
                #if tok.type == 'NEWLINE' or tok.type == 'SEMICOLON':
                    #if tok.type == 'NEWLINE' and ignore_newline:
                        #ignore_newline = True
                        #continue
                    #state = 'idle'
                    #if len(expr) > 0:
                        #command.append(expr)
                    #expr = ''
                    ##if command and command[0] == 'source':
                    ##    p = TclParser()
                    ##    try:
                    ##        p.input_file(command[1])
                    ##        commands.extend(p.parse())
                    ##    except IOError:
                    ##        if len(command) > 0:
                    ##            commands.append(command)
                    ##            command = []

                    ##else:
                    #if len(command) > 0:
                        #commands.append(command)
                        #command = []
                #elif tok.type == 'BACKSLASH':
                    #ignore_newline = True
                #elif tok.type == 'WHITESPACE':
                    #ignore_newline = False
                    #if len(expr) > 0:
                        #command.append(expr)
                        #expr = ''
                #elif tok.type == 'LBRACKET':
                    #ignore_newline = False
                    ##print "lbracket"
                    ##print commands
                    #depth += 1
                    #if len(expr) > 0:
                        #command.append(expr)
                        #expr = ''
                    ##print command
                    #commands_stack.append(commands)
                    #commands = command
                    #command = []
                    ##print commands
                    ##print command

                #elif tok.type == 'RBRACKET':
                    #ignore_newline = False
                    ##print "rbracket"
                    ##print commands
                    #if len(expr) > 0:
                        #command.append(expr)
                        #expr = ''
                    ##print command

                    #commands.append(command)
                    #command = []
                    ##print commands
                    ##print command
                    #last_commands = commands_stack.pop()
                    #last_commands.append(commands)
                    #commands = last_commands
                    ##print "last one"
                    ##print commands
                    ##print command
                    #depth -= 1
                #else:
                    #ignore_newline = False
                    #expr += tok.value

        #return commands

