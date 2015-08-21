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
        self.include_stack = []
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

    def setcwd(self,path):
        os.chdir(path)

    def try_log_debug(self,*args):
        try:
            self.logger.debug(args)
        except AttributeError:
            pass

    def run(self):
        return self.run_on_file(self.filename)

    def run_on_file(self,filename):
        self.include_stack.append(filename)
        self.current_filename = filename
        try:
            self.logger.info("==== Running on file: %s",filename)
        except AttributeError:
            pass
        data = ''
        with open(filename) as f:
            for line in f:
                data += line

        ret_value = self.run_on_string(data)
        self.include_stack.pop()
        if len(self.include_stack) > 0:
            self.current_filename = self.include_stack[-1]

        return ret_value

    def run_on_string(self,data):

        self.try_log_debug("==== Running on string\n%s...\n",data[:200])

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
        script = parser.parse(lexer=lex,debug=self.logger)
        #print script
        return script

        #while 1:
            #try:
                #self.parser.parse(data)
            #except TypeError as e:
                #print e
                #break


class TclParser(Parser):

    tokens = (
            'WHITESPACE',
            'NEWLINE',
            'SEMICOLON',
            'BACKSLASH',
            'LBRACKET',
            'QUOT',
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
    #t_RPAREN = r'\)'
    t_RBRACKET = r'\]'
    t_LBRACE = r'\{'
    t_RBRACE = r'\}'
    t_DOLLAR = r'\$'
    t_LETTER = r'[a-zA-Z]'
    t_DIGIT = r'\d'
    t_COLON = r'\:+'
    t_UNDER = r'\_'
    t_BRACKET = r'[\(\)]'
    t_OTHER = r'[@\&\|\-\/\.\!\=\+\<\>\*\)\,]'

    def __init__(self,filename,waf_env,**kw):
        Parser.__init__(self,filename,**kw)
        self.waf_env = waf_env
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
            p[0] = p[1] + [p[2]]
        else:
            p[0] = [p[1]]

    def p_commandend(self,p):
        '''commandend : NEWLINE
                      | SEMICOLON'''
        p[0] = p[1]


    def p_string_text(self,p):
        '''string : string string
                  | string replace
                  | string LETTER
                  | string DIGIT
                  | string OTHER
                  | string UNDER
                  | string COLON
                  | LETTER
                  | DIGIT
                  | OTHER
                  | UNDER
                  | COLON
                  | string BRACKET
                  | BRACKET'''
        if len(p) == 3:
            p[0] = p[1] + p[2]
        else:
            p[0] = p[1]

    def p_backslashreplace(self,p):
        '''replace : BACKSLASH LETTER
                   | BACKSLASH LBRACKET
                   | BACKSLASH RBRACKET
                   | BACKSLASH UNDER
                   | BACKSLASH DIGIT'''
        p[0] = self.replace_backslash(p[2])

    def p_longwhitespace(self,p):
        '''longwhite : BACKSLASH NEWLINE'''
        p[0] = ''

    def p_longwhitespace_cont(self,p):
        '''longwhite : longwhite WHITESPACE'''
        p[0] = p[1] + p[2]

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
                    | variable COLON
                    | DOLLAR LETTER
                    | DOLLAR DIGIT
                    | DOLLAR UNDER
                    | DOLLAR COLON'''
#                    | variable BRACKET

        if len(p) == 3:
            p[0] = p[1] + p[2]
        else:
            p[0] = p[1]

    def p_brace_variable(self,p):
        '''bracevariable : bracevariable LBRACE
                    | bracevariable LETTER
                    | bracevariable DIGIT
                    | bracevariable UNDER
                    | bracevariable COLON
                    | DOLLAR LBRACE'''
#                    | bracevariable BRACKET
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
                    | quotword longwhite
                    | quotword replace
                    | quotword COLON
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
                       | bracestring LBRACKET
                       | bracestring RBRACKET
                       | bracestring commandend
                       | bracestring WHITESPACE
                       | bracestring longwhite
                       | bracestring QUOT
                       | bracestring BRACKET
                       | bracestring BACKSLASH
                       | bracestring OTHER
                       | bracestring UNDER
                       | bracestring DOLLAR
                       | bracestring COLON
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
            error_string = "Syntax error at token %s(%s)" % (p.type,p.value)
            error_string += " at line %d, pos %d in" % (p.lineno,p.lexpos)
            error_string += " in file %s" % (self.current_filename)
            if len(self.include_stack) > 1:
                for file in self.include_stack[:-1]:
                    error_string += "\n included from file %s" % (file)
            raise TypeError(error_string)
        else:
            print("Syntax error at EOF")

    def replace_variable(self,name):
        try:
            if name.find('{') == 1:
                self.try_log_debug("Replacing Variable "+name[2:-1]+" to "+
                        str(self.variables[name[2:-1]]))
                return self.variables[name[2:-1]]
            else:
                self.try_log_debug("Replacing Variable "+name[1:]+" to "+
                        str(self.variables[name[1:]]))
                return self.variables[name[1:]]
        except KeyError:
            error_string = "You have to define variable %s first" % (name[1:])
            error_string += " in file %s" % (self.current_filename)
            raise Exception(error_string)
            #print "You have to define variable %s first" % (m.group(1))


    def evaluate_condition(self,cond):
        not_re = re.compile(r'\!\s*([\w\d])')
        m = not_re.search(cond)
        if m:
            cond = not_re.sub(' not '+m.group(1),cond)
        #cond = cond.replace(r'!\s?([\w\d])',' not \g1')
        self.try_log_debug("Condition "+cond)
        try:
            self.try_log_debug("Evaluates to "+str(eval(cond)))
            return eval(cond)
        except:
            return False

    def replace_backslash(self,afterslash):
        return afterslash

    def interpret(self,p,commandpos):
        command = p[commandpos]

        if command[0] == 'set':
            assert(len(command) == 3)
            if command[2] is None:
                self.variables[command[1]] = ""
            else:
                self.variables[command[1]] = command[2]
            self.try_log_debug("Setting variable %s to %s",command[1],command[2])
        elif command[0] == 'puts':
            if len(command) == 2:
                print command[2]
        elif command[0] == 'getenv':
            assert(len(command) == 2)
            if command[1] in os.environ:
                return os.environ[command[1]]
            elif command[1] in self.waf_env:
                return self.waf_env[command[1]]
            else:
                raise Exception("Environment variable "+command[1]+" not found in getenv")
        elif command[0] == 'source':
            assert(len(command) == 2)
            self.run_on_file(command[1])
        elif command[0] == 'if':
            condition = self.run_on_string(command[1])[0]
            self.try_log_debug(condition)
            condition = "".join(self.run_on_string(command[1])[0])
            if self.evaluate_condition(condition):
                self.run_on_string(command[2])
            else:
                if len(command) > 3 and command[3] == 'else':
                    self.run_on_string(command[4])
        elif command[0] == 'expr':
            try:
                return str(eval("".join(command[1:])))
            except:
                return ""
        else:
            return ""

class EncounterTclParser(TclParser):
    def __init__(self,filename,waf_env,**kw):
        TclParser.__init__(self,filename,waf_env,**kw)
        self.output_files = []

    def interpret(self,p,commandpos):
        command = p[commandpos]
        try:
            self.logger.info(command)
        except AttributeError:
            pass

        if command[0] in [
                'saveDesign',
                'writeSdf',
                'rcOut',
                'saveNetlist',
                'write_sdc']:
            for word in command[1:]:
                if word[0] == '-':
                    continue
                else:
                    self.output_files.append(word)
        elif command[0] == 'list':
            assert(len(command[1:]) > 0)
            #ret_string = ""
            ret_list = []
            for word in command[1:]:
                #ret_string += word
                ret_list.append(word)
            return ret_list
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
