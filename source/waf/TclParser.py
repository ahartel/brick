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
        self.logger = kw.get('logger',None)
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
        #self.parser = yacc.yacc(module=self,
                  #debug=self.debug,
                  #debugfile=self.debugfile,
                  #tabmodule=self.tabmodule)

    def run(self,debug=None):
        return self.run_on_file(self.filename,debug=debug)

    def run_on_file(self,filename,debug=None):
        self.logger.debug("Running on file: "+filename)
        data = ''
        with open(filename) as f:
            for line in f:
                data += line

        return self.run_on_string(data,debug=debug)

    def run_on_string(self,data,debug=None):
        self.logger.debug("Running on string "+data)
        lex  = self.lexer.clone()
        #lexer debugging
        lex.input(data)

        if 0:
            tok = lex.token()
            while tok:
                print tok
                tok = lex.token()
            lex.lineno = 1
            lex.input(data)

        parser = yacc.yacc(module=self,
                  debug=self.debug,
                  debugfile=self.debugfile,
                  tabmodule=self.tabmodule)
        #try:
            #self.parser.restart()
        #except AttributeError:
            #pass
        return parser.parse(lexer=lex,debug=debug)

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
            'DOLLAR',
            'LETTER',
            'DIGIT',
            'COLON',
            'UNDER',
            'BRACKET',
            'OTHER'
        )

    t_WHITESPACE = r'[ \t]'
    t_SEMICOLON = r';'
    t_BACKSLASH = r'\\'
    t_LBRACKET = r'\['
    t_QUOT = r'"'
    t_RPAREN = r'\)'
    t_RBRACKET = r'\]'
    t_LBRACE = r'\{'
    t_RBRACE = r'\}'
    t_DOLLAR = r'\$'
    t_LETTER = r'[a-zA-Z]'
    t_DIGIT = r'\d'
    t_COLON = r'\:+'
    t_UNDER = r'\_'
    t_BRACKET = r'[\(\)]'
    t_OTHER = r'[\-\/\.\!\=\+\<\>]'

    def __init__(self,filename,**kw):
        Parser.__init__(self,filename,**kw)
        self.logger = kw.get('logger', None)
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
        #self.pp.pprint(self.variables)
        #print p[1]
        p[0] = p[1]

    def p_script(self,p):
        '''script : script script
                  | script command
                  | command'''
        if len(p) == 3:
            p[0] = p[1] + p[2]
        else:
            p[0] = [p[1]]

    def p_commandend(self,p):
        '''commandend : NEWLINE
                      | SEMICOLON'''
        p[0] = p[1]


    def p_string_text(self,p):
        '''string : string string
                  | string LETTER
                  | string DIGIT
                  | string OTHER
                  | string UNDER
                  | LETTER
                  | DIGIT
                  | OTHER
                  | UNDER'''
        if len(p) == 3:
            p[0] = p[1] + p[2]
        else:
            p[0] = p[1]


    def p_longwhitespace(self,p):
        '''longwhite : BACKSLASH NEWLINE'''
        p[0] = ''

    def p_longwhitespace_cont(self,p):
        '''longwhite : longwhite WHITESPACE'''
        p[0] = p[1] + p[2]

    def p_backslash(self,p):
        '''string : BACKSLASH LETTER
                  | BACKSLASH LBRACKET
                  | BACKSLASH UNDER'''
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

    def p_variable(self,p):
        '''variable : variable LETTER
                    | variable DIGIT
                    | variable UNDER
                    | variable BRACKET
                    | variable COLON
                    | DOLLAR LETTER
                    | DOLLAR DIGIT
                    | DOLLAR UNDER
                    | DOLLAR COLON'''

        if len(p) == 3:
            p[0] = p[1] + p[2]
        else:
            p[0] = p[1]

    def p_brace_variable(self,p):
        '''bracevariable : bracevariable LBRACE
                    | bracevariable LETTER
                    | bracevariable DIGIT
                    | bracevariable UNDER
                    | bracevariable BRACKET
                    | bracevariable COLON
                    | DOLLAR LBRACE'''
        p[0] = p[1] + p[2]

    def p_quotword_start(self,p):
        '''quotword : QUOT'''
        p[0] = ''

    def p_quotword_cont(self,p):
        '''quotword : quotword LETTER
                    | quotword DIGIT
                    | quotword commandend
                    | quotword WHITESPACE
                    | quotword LBRACE
                    | quotword UNDER
                    | quotword OTHER
                    | quotword RBRACE'''
        p[0] = p[1] + p[2]

    def p_quotword_bracevariable(self,p):
        '''quotword : quotword bracevariable RBRACE'''
        p[0] = p[1] + self.replace_variable(p[2]+p[3])

    def p_quotword_variable(self,p):
        '''quotword : quotword variable'''
        p[0] = p[1] + self.replace_variable(p[2])

    def p_quotword_end(self,p):
        '''word : quotword QUOT'''
        #print 'word',p[1]
        p[0] = p[1]

    def p_braceword_start(self,p):
        '''bracestring : LBRACE'''
        p[0] = p[1]

    def p_braceword_cont(self,p):
        '''bracestring : bracestring LETTER
                       | bracestring DIGIT
                       | bracestring commandend
                       | bracestring WHITESPACE
                       | bracestring longwhite
                       | bracestring QUOT
                       | bracestring BACKSLASH
                       | bracestring OTHER
                       | bracestring UNDER
                       | bracestring DOLLAR
                       | bracestring braceword'''
        p[0] = p[1] + p[2]
        #print "bracestring",p[0]

    def p_braceword_end(self,p):
        '''braceword : bracestring RBRACE'''
        p[0] = p[1]+ p[2]
        #print "braceword",p[0]


    def p_braceword_word(self,p):
        '''word : braceword'''

        p[0] = re.sub(r'^\{','',p[1])
        p[0] = re.sub(r'\}$','',p[0])

    def p_command_word(self,p):
        '''command : wordlist commandend
                   | wordlist'''

        p[0] = p[1]
        self.interpret(p,0)

    def p_empty_command(self,p):
        '''command : commandend
                   | WHITESPACE'''
        p[0] = []

    def p_word_list(self,p):
        '''wordlist : wordlist word
                    | word'''
        if len(p) == 3:
            p[0] = p[1] + [p[2]]
        else:
            p[0] = [p[1]]

    def p_sring_bracevariable(self,p):
        '''string : bracevariable RBRACE'''
        p[0] = self.replace_variable(p[1]+p[2])

    def p_string_variable(self,p):
        '''string : variable'''
        p[0] = self.replace_variable(p[1])

    def p_word_string(self,p):
        '''word : word longwhite
                | word WHITESPACE
                | string WHITESPACE
                | string longwhite
                | string'''
        p[0] = p[1]

    def p_empty(self,p):
        'empty : '
        pass

    def p_error(self,p):
        if p:
            #print("Syntax error at token", p.type)
            # Just discard the token and tell the parser it's okay.
            #self.parser.errok()
            raise TypeError("Syntax error at token %s(%s) at line %d, pos %d" % (p.type,p.value,p.lineno,p.lexpos))
        else:
            print("Syntax error at EOF")

    def replace_variable(self,name):
        try:
            if name.find('{') == 1:
                self.logger.debug("Replacing Variable "+name[2:-1]+" to "+self.variables[name[2:-1]])
                return self.variables[name[2:-1]]
            else:
                self.logger.debug("Replacing Variable "+name[1:]+" to "+self.variables[name[1:]])
                return self.variables[name[1:]]
        except KeyError:
            raise Exception("You have to define variable %s first" % (name[1:]))
            #print "You have to define variable %s first" % (m.group(1))


    def evaluate_condition(self,cond):
        self.logger.debug("Condition "+cond)
        self.logger.debug("Evaluates to "+str(eval(cond)))
        return eval(cond)

    def interpret(self,p,commandpos):
        command = p[commandpos]

        if command[0] == 'set':
            assert(len(command) == 3)
            self.variables[command[1]] = command[2]
            print "Setting variable",command[1],"to",command[2]
        elif command[0] == 'getenv':
            assert(len(command) == 2)
            return os.environ[command[1]]
        elif command[0] == 'source':
            assert(len(command) == 2)
            self.run_on_file(command[1])
        elif command[0] == 'if':
            condition = self.run_on_string(command[1])[0]
            self.logger.debug(condition)
            condition = "".join(self.run_on_string(command[1])[0])
            if self.evaluate_condition(condition):
                self.run_on_string(command[2])
            else:
                if command[3] == 'else':
                    self.run_on_string(command[4])


class EncounterTclParser(TclParser):
    def __init__(self,filename,**kw):
        TclParser.__init__(self,filename,**kw)
        self.output_files = []

    def interpret(self,p,commandpos):
        command = p[commandpos]
        self.logger.debug(command)

        if command[0] == 'saveDesign':
            for word in command[1:]:
                if word[0] == '-':
                    continue
                else:
                    self.output_files.append(word)
        elif command[0] == 'list':
            assert(len(command[1:]) > 0)
            ret_string = ""
            for word in command[1:]:
                ret_string += word
            return ret_string
        elif command[0] == 'append':
            assert(len(command) >= 3)
            ret_string = command[1]
            for word in command[2:]:
                ret_string += command[2]
            return ret_string
        else:
            return TclParser.interpret(self,p,commandpos)

    def get_output_files(self):
        return self.output_files
