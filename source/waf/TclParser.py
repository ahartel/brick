import ply.lex as lex

class TclParser():

    def __init__(self):
        tokens = (
                'COMMENT',
                'TEXT',
                'LBRACE',
                'RBRACE',
                'LBRACKET',
                'RBRACKET',
                'QUOT',
                'NEWLINE',
                'SEMICOLON',
                'BACKSLASH',

                'DEREFERENCE',
                'SLASH',
                'NUMBER',
                'WHITESPACE',
                'GREATER',
                'EQUALS',
                'LPAREN',
                'RPAREN',
                'NUMOP',
            )

        t_BACKSLASH = r'\\'
        t_LBRACE = r'\{'
        t_RBRACE = r'\}'
        t_TEXT = r'[:!\'.\w]+'
        t_NUMOP = r'[\*\+\-]'
        t_EQUALS = r'='
        t_GREATER = r'>'
        t_SLASH = r'\/'
        t_LPAREN = r'\('
        t_RPAREN = r'\)'
        t_LBRACKET = r'\['
        t_RBRACKET = r'\]'
        t_QUOT = r'"'
        t_NEWLINE = r'\n'
        t_SEMICOLON = r';'
        t_DEREFERENCE = r'\$'
        t_WHITESPACE = r'[ \t]+'

        def t_NUMBER(t):
            r'\d+'
            #t.value = int(t.value)
            #return t
            pass

        def t_COMMENT(t):
            r'\#.*'
            pass

        # Error handling rule
        def t_error(t):
            print "Illegal character '%s'" % t.value[0]
            t.lexer.skip(1)

        self.lexer = lex.lex()

    def input_file(self,name):
        print name
        data = ''
        with open(name) as f:
            for line in f:
                data += line

        self.input(data)

    def input(self,data):
        self.lexer.input(data)

    def token(self):
        return self.lexer.token()

    def parse(self):
        state = 'idle'
        commands = []
        command = []
        commands_stack = []
        expr = ''
        depth = 0
        ignore_newline = False
        while True:
            tok = self.token()
            if not tok: break
            #if tok.type == 'NEWLINE' and len(commands) == 20:
            #    print commands
            #    print command
            #    break
            #print commands
            #print command
            #print tok
            if state == 'idle':
                if tok.type == 'TEXT':
                    state = 'command'
                    expr += tok.value
                    depth = 0
                    command = []
            elif state == 'command':
                if tok.type == 'NEWLINE' or tok.type == 'SEMICOLON':
                    if tok.type == 'NEWLINE' and ignore_newline:
                        ignore_newline = True
                        continue
                    state = 'idle'
                    if len(expr) > 0:
                        command.append(expr)
                    expr = ''
                    #if command and command[0] == 'source':
                    #    p = TclParser()
                    #    try:
                    #        p.input_file(command[1])
                    #        commands.extend(p.parse())
                    #    except IOError:
                    #        if len(command) > 0:
                    #            commands.append(command)
                    #            command = []

                    #else:
                    if len(command) > 0:
                        commands.append(command)
                        command = []
                elif tok.type == 'BACKSLASH':
                    ignore_newline = True
                elif tok.type == 'WHITESPACE':
                    ignore_newline = False
                    if len(expr) > 0:
                        command.append(expr)
                        expr = ''
                elif tok.type == 'LBRACKET':
                    ignore_newline = False
                    #print "lbracket"
                    #print commands
                    depth += 1
                    if len(expr) > 0:
                        command.append(expr)
                        expr = ''
                    #print command
                    commands_stack.append(commands)
                    commands = command
                    command = []
                    #print commands
                    #print command

                elif tok.type == 'RBRACKET':
                    ignore_newline = False
                    #print "rbracket"
                    #print commands
                    if len(expr) > 0:
                        command.append(expr)
                        expr = ''
                    #print command

                    commands.append(command)
                    command = []
                    #print commands
                    #print command
                    last_commands = commands_stack.pop()
                    last_commands.append(commands)
                    commands = last_commands
                    #print "last one"
                    #print commands
                    #print command
                    depth -= 1
                else:
                    ignore_newline = False
                    expr += tok.value

        return commands

