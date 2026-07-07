with open('tests/test_update_readme.py', 'r') as f:
    content = f.read()

content = content.replace('class TestUpdateReadme(unittest.TestCase):', 'class TestUpdateReadme(unittest.TestCase):\n    # pylint: disable=too-many-public-methods')
content = content.replace('    def test_load_yaml_success(self, mock_file):', '    def test_load_yaml_success(self, _mock_file):')
content = content.replace('    def test_load_yaml_not_found(self, mock_print, mock_file):', '    def test_load_yaml_not_found(self, mock_print, _mock_file):')
content = content.replace('    def test_load_yaml_error(self, mock_print, mock_file):', '    def test_load_yaml_error(self, mock_print, _mock_file):')

with open('tests/test_update_readme.py', 'w') as f:
    f.write(content)
