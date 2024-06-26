import unittest
from unittest.mock import patch, MagicMock

class TestMyGPTScript(unittest.TestCase):
    
    @patch('mygpt_script.requests.get')
    def test_get_changed_files(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{'filename': 'test_file.py'}]
        mock_get.return_value = mock_response

        from mygpt_script import get_changed_files
        files = get_changed_files(1)
        self.assertIn('test_file.py', files)

    @patch('mygpt_script.openai.ChatCompletion.create')
    def test_analyze_code(self, mock_create):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = {'content': 'Analysis result'}
        mock_create.return_value = mock_response

        from mygpt_script import analyze_code
        result = analyze_code('test_file.py')
        self.assertEqual(result, 'Analysis result')

    @patch('mygpt_script.openai.ChatCompletion.create')
    def test_generate_witty_comment(self, mock_create):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = {'content': 'Witty comment'}
        mock_create.return_value = mock_response

        from mygpt_script import generate_witty_comment
        result = generate_witty_comment()
        self.assertEqual(result, 'Witty comment')

    @patch('mygpt_script.requests.post')
    def test_post_comment_to_pr(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        from mygpt_script import post_comment_to_pr
        post_comment_to_pr(1, 'Test comment')
        mock_post.assert_called_once()

if __name__ == '__main__':
    unittest.main()
