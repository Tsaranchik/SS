import re
from typing import List, Tuple
import json


class CCodeAnalyzer:
    def __init__(self, code : str):
        self._code = code

        self._keywords = {'int', 'if', 'else', 'while', 'void', 'do', 'return'}
        self._patterns = {
            'IDENTIFIER' : re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*'),
            'NUMBER' : re.compile(r'\d+'),
            'STRING_LITERAL': re.compile(r'"([^"\\]*(\\.[^"\\]*)*)"', re.DOTALL),
            'FORMAT_SPECIFIER' : re.compile(r'%[diouxXeEfFgGcs]'),
            'OPERATOR' : re.compile(r'[+\-*/%&|^=<>!~]'),
            'SEMICOLON' : re.compile(r';'),
            'INCLUDE' : re.compile(r'#\s*include\s*<([a-zA-Z0-9_]+\.h)>'),
            'LPAREN' : re.compile(r'\('),
            'RPAREN' : re.compile(r'\)'),
            'LBRACE' : re.compile(r'\{'),
            'RBRACE' : re.compile(r'\}'),
        }

        self._variable_counter = 0
        self._variable_ids = {}
        self._bracket_stack = []
        self._expected_semicolon = False
        self.tokens = []
        self._do_stack = []
    

    def _classify_token(self, token):

        if token in self._keywords:
            return ('KEYWORD', token)
        
        for token_type, pattern in self._patterns.items():
            if isinstance(pattern, re.Pattern) and pattern.match(token):
                if token_type == 'LPAREN':
                    self._bracket_stack.append('(')

                elif token_type == 'RPAREN':
                    if self._bracket_stack and self._bracket_stack[-1] == '(':
                        self._bracket_stack.pop()
                    else:
                        raise SyntaxError('Unmatched parenthesis')
                        
                elif token_type == 'LBRACE':
                    self._bracket_stack.append('{')
                    
                elif token_type == 'RBRACE':
                    if self._bracket_stack and self._bracket_stack[-1] == '{':
                        self._bracket_stack.pop()
                    else:
                        raise SyntaxError('Unmatched brace')
                
                elif self._patterns['IDENTIFIER'].match(token):
                    if token not in self._variable_ids:
                        self._variable_counter += 1
                        self._variable_ids[token] = f'id_{self._variable_counter}'
                    
                    return ('IDENTIFIER', token, self._variable_ids[token])
                
                elif self._patterns['INCLUDE'].match(token):
                    return ('INCLUDE', self._patterns['INCLUDE'].findall(token)[0])
                
                elif self._patterns['FORMAT_SPECIFIER'].match(token):
                    return ('FORMAT_SPECIFIER', token)
                
                elif self._patterns['STRING_LITERAL'].match(token):
                    string_content = self._patterns['STRING_LITERAL'].findall(token)[0][0]
                    format_specifiers = self._patterns['FORMAT_SPECIFIER'].findall(string_content)
                    if format_specifiers:
                        return ('STRING_WITH_FORMAT_SPECIFIERS', string_content, format_specifiers)
                    return ('STRING_LITERAL', string_content)
                    
                return (token_type, token)

        return ('UNKNOWN', token)
    

    def _tokenize(self):
        tokens = re.findall(r'#[^\n]*|"(?:[^"\\]|\\.)*"|%[diouxXeEfFgGcs]|[a-zA-Z_][a-zA-Z0-9_]*|\d+|[+\-*/%&|^=<>!~]+|[{}();]|#\s*include\s*<.*?>', self._code)
        classified_tokens = [self._classify_token(token) for token in tokens]

        for i in range(len(classified_tokens) - 1):
            if classified_tokens[i + 1][1] == '(':
                if classified_tokens[i - 1][0] == 'KEYWORD' and classified_tokens[i - 1][1] == 'int':
                    classified_tokens[i] = ('FUNCTION_DEFINITION', classified_tokens[i][1])

                    # Я НЕ ПОНИМАЮ, ЧТО Я ДЕЛАЮ, ПОМОГИТЕ
                    # Я ПЫТАЮСЬ ПОФИКСИТЬ ID-ШНИКИ И Я НЕ ЗНАЮ КАК ЭТО СДЕЛАТЬ ИНАЧЕ
                    self._variable_counter -= 1
                    del self._variable_ids[classified_tokens[i][1]]

                    counter = 1
                    for id in self._variable_ids:
                        self._variable_ids[id] = f'id_{counter}'
                        counter += 1

                elif classified_tokens[i][0] == 'IDENTIFIER':
                    classified_tokens[i] = ('FUNCTION_CALL', classified_tokens[i][1])

                    self._variable_counter -= 1
                    del self._variable_ids[classified_tokens[i][1]]

                    counter = 1
                    for id in self._variable_ids:
                        self._variable_ids[id] = f'id_{counter}'
                        counter += 1
        
        # СЮДА НЕ СМОТРЕТЬ - СТРАШНАЯ ВЕЩЬ 
        for i in range(len(classified_tokens) - 1):
            if len(classified_tokens[i]) == 3:
                for id in self._variable_ids:
                    if id == classified_tokens[i][1]:
                        classified_tokens[i] = (classified_tokens[i][0], id, self._variable_ids[id])
        
        if self._bracket_stack:
            raise SyntaxError(f'Unmatched brackets: {self._bracket_stack}')
        
        return classified_tokens
    
    def _validate_semicolons(self, tokens):
        for i in range(len(tokens) - 1):
            token_type, token_value = tokens[i][0], tokens[i][1]
            
            if token_type == 'FUNCTION_DEFINITION':
                if self._expected_semicolon:
                    self._expected_semicolon = False
            
            if token_type == 'RPAREN' and i + 1 < len(tokens):
                if tokens[i + 1][0] != 'LBRACE' and tokens[i + 1][0] != 'SEMICOLON':
                    raise SyntaxError(f"Missing semicolon after '{token_value}'")
            
            if token_type == 'KEYWORD' and token_value in self._keywords:
                if i + 1 < len(tokens) and tokens[i + 1][0] == 'IDENTIFIER':
                    self._expected_semicolon = True
            
            if self._expected_semicolon and token_type == 'SEMICOLON':
                if self._expected_semicolon:
                    self._expected_semicolon = False
            
            if token_type in ('IDENTIFIER', 'NUMBER') and i + 1 < len(tokens):
                next_token_type = tokens[i + 1][0]
                if next_token_type not in ('OPERATOR', 'SEMICOLON', 'RPAREN'):
                    raise SyntaxError(f"Missing semicolon after '{token_value}'")
                
            if token_type == 'KEYWORD' and token_value == 'do':
                self._do_stack.append(i)
                if i + 1 < len(tokens) and tokens[i + 1][0] == 'LBRACE':
                    continue
            
            if token_type == 'KEYWORD' and token_value == 'while':
                if self._do_stack:
                    self._do_stack.pop()
                    self._expected_semicolon = True
        
        if self._do_stack:
            raise SyntaxError("Unmatched 'do' without a corresponding 'while'")
                    
    
    def _convert_to_json(self, tokens, json_file_name):
        json_data = []
        for token_info in tokens:
            token_entry = {'type' : token_info[0], 'value' : token_info[1]}
            if token_info[0] == 'IDENTIFIER':
                token_entry['id'] = token_info[2]
            if token_info == 'STRING_WITH_FORMAT_SPECIFIERS':
                token_entry['format_specifiers'] = token_info[2]
            
            json_data.append(token_entry)
        
        json_data_dict = {"Literals" : json_data}
        
        with open(json_file_name, 'w') as fp:
            json.dump(json_data_dict, fp, indent=4)
        return json.dumps(json_data_dict, indent=4)


    def analyze(self):
        tokens = self._tokenize()
        self._validate_semicolons(tokens)
        json_output = self._convert_to_json(tokens, 'data.json')
        return json_output
