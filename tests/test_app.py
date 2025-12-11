import os
import sys
import json
import tempfile
import urllib.parse
from unittest.mock import patch, Mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.app import app, parse_forms_from_url, save_to_file


# ==================== Тесты для вспомогательных функций ====================


def test_save_to_file():
    """Сохранение данных в файл"""
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", delete=False, suffix=".json"
    ) as f:
        temp_path = f.name

    try:
        test_data = [
            {"name": "form1", "inputs": [{"name": "field1"}]},
            {"name": "form2", "inputs": [{"name": "field2"}]},
        ]

        save_to_file(test_data, temp_path)

        assert os.path.exists(temp_path)

        with open(temp_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data == test_data
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_save_to_file_unicode():
    """Сохранение данных с Unicode символами"""
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", delete=False, suffix=".json"
    ) as f:
        temp_path = f.name

    try:
        test_data = [
            {"name": "формы", "description": "тест с русскими буквами и emoji 🚀"}
        ]

        save_to_file(test_data, temp_path)

        with open(temp_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data == test_data
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_parse_forms_from_url_success():
    """Успешное извлечение форм из URL"""
    with patch("src.app.fetch_html") as mock_fetch, patch(
        "src.app.extract_forms"
    ) as mock_extract:

        mock_fetch.return_value = "<html><form></form></html>"
        mock_extract.return_value = [
            Mock(to_dict=lambda: {"id": "form1", "inputs": []}),
            Mock(to_dict=lambda: {"id": "form2", "inputs": []}),
        ]

        result = parse_forms_from_url("http://example.com")

        assert result["forms_count"] == 2
        assert result["html_length"] == len("<html><form></form></html>")
        assert len(result["forms"]) == 2
        assert result["forms"][0]["id"] == "form1"


def test_parse_forms_from_url_no_html():
    """Ошибка при получении HTML"""
    with patch("src.app.fetch_html") as mock_fetch:
        mock_fetch.return_value = None

        try:
            parse_forms_from_url("http://example.com")
            assert False, "Должно было возникнуть исключение"
        except ConnectionError as e:
            assert "Couldn't get html" in str(e)


# ==================== Тесты для Flask endpoint ====================


def test_api_parse_missing_url():
    """Отсутствует параметр URL"""
    with app.test_client() as client:
        response = client.get("/api/parse")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "missing url parameter" in data["error"]


def test_api_parse_success():
    """Успешный парсинг форм"""
    with patch("src.app.fetch_html") as mock_fetch, patch(
        "src.app.extract_forms"
    ) as mock_extract, patch("src.app.save_scan") as mock_save_scan, patch(
        "src.app.save_to_file"
    ) as mock_save_file:

        mock_fetch.return_value = "<html><form id='test'></form></html>"
        mock_extract.return_value = [
            Mock(to_dict=lambda: {"id": "form1", "action": "/submit", "inputs": []})
        ]
        mock_save_scan.return_value = 12345

        with app.test_client() as client:
            response = client.get("/api/parse?url=http://example.com")

            assert response.status_code == 200
            data = json.loads(response.data)

            assert data["count"] == 1
            assert data["scan_id"] == 12345
            assert len(data["forms"]) == 1
            assert data["forms"][0]["id"] == "form1"

            mock_fetch.assert_called_once_with("http://example.com")
            mock_extract.assert_called_once_with(
                "<html><form id='test'></form></html>", "http://example.com"
            )
            mock_save_scan.assert_called_once()
            mock_save_file.assert_called_once()


def test_api_parse_fetch_error():
    """Ошибка при получении HTML"""
    with patch("src.app.fetch_html") as mock_fetch:
        mock_fetch.return_value = None

        with app.test_client() as client:
            response = client.get("/api/parse?url=http://example.com")

            assert response.status_code == 400
            data = json.loads(response.data)
            assert "error" in data
            assert "Couldn't get html" in data["error"]


def test_api_parse_extract_error():
    """Ошибка при извлечении форм"""
    with patch("src.app.fetch_html") as mock_fetch, patch(
        "src.app.extract_forms"
    ) as mock_extract:

        mock_fetch.return_value = "<html></html>"
        mock_extract.side_effect = Exception("Parsing error")

        with app.test_client() as client:
            response = client.get("/api/parse?url=http://example.com")

            assert response.status_code == 400
            data = json.loads(response.data)
            assert "error" in data
            assert "Parsing error" in data["error"]


def test_api_parse_file_url():
    """Парсинг форм из file:// URL"""
    with patch("src.app.fetch_html") as mock_fetch, patch(
        "src.app.extract_forms"
    ) as mock_extract, patch("src.app.save_scan") as mock_save_scan, patch(
        "src.app.save_to_file"
    ) as mock_save_file:

        mock_fetch.return_value = "<html><form></form></html>"
        mock_extract.return_value = []
        mock_save_scan.return_value = 999

        with app.test_client() as client:
            response = client.get("/api/parse?url=file:///path/to/file.html")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["count"] == 0
            assert data["scan_id"] == 999


def test_api_parse_empty_forms():
    """Парсинг страницы без форм"""
    with patch("src.app.fetch_html") as mock_fetch, patch(
        "src.app.extract_forms"
    ) as mock_extract, patch("src.app.save_scan") as mock_save_scan:

        mock_fetch.return_value = "<html><body>No forms here</body></html>"
        mock_extract.return_value = []
        mock_save_scan.return_value = 777

        with app.test_client() as client:
            response = client.get("/api/parse?url=http://example.com")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["count"] == 0
            assert data["forms"] == []
            assert data["scan_id"] == 777


def test_api_parse_with_encoding():
    """Парсинг URL с параметрами и кодированием"""
    with patch("src.app.fetch_html") as mock_fetch, patch(
        "src.app.extract_forms"
    ) as mock_extract, patch("src.app.save_scan") as mock_save_scan:

        mock_fetch.return_value = "<html></html>"
        mock_extract.return_value = []
        mock_save_scan.return_value = 1

        with app.test_client() as client:
            # Правильное кодирование URL с несколькими параметрами
            url = "https://example.com/search?q=test+query&page=1"
            encoded_url = urllib.parse.quote(url, safe="")
            response = client.get(f"/api/parse?url={encoded_url}")

            assert response.status_code == 200
            mock_fetch.assert_called_once_with(
                "https://example.com/search?q=test+query&page=1"
            )


def test_api_parse_invalid_url_format():
    """Некорректный формат URL"""
    with patch("src.app.fetch_html") as mock_fetch:
        mock_fetch.side_effect = Exception("Invalid URL")

        with app.test_client() as client:
            response = client.get("/api/parse?url=not-a-valid-url")

            assert response.status_code == 400
            data = json.loads(response.data)
            assert "error" in data
            assert "Invalid URL" in data["error"]


def test_api_parse_save_scan_metadata():
    """Проверка метаданных при сохранении сканирования"""
    import tempfile

    # Создаем временную директорию для тестового файла
    temp_dir = tempfile.mkdtemp()
    test_data_dir = os.path.join(temp_dir, "tests", "test_data")
    os.makedirs(test_data_dir, exist_ok=True)

    try:
        with patch("src.app.fetch_html") as mock_fetch, patch(
            "src.app.extract_forms"
        ) as mock_extract, patch("src.app.save_scan") as mock_save_scan, patch(
            "src.app.save_to_file"
        ) as mock_save_file:

            html_content = "<html><form></form><form></form></html>"
            mock_fetch.return_value = html_content
            mock_extract.return_value = [
                Mock(to_dict=lambda: {"id": "form1"}),
                Mock(to_dict=lambda: {"id": "form2"}),
            ]

            with app.test_client() as client:
                response = client.get("/api/parse?url=http://example.com")

                assert response.status_code == 200

                # Проверяем вызов save_scan
                call_args = mock_save_scan.call_args
                assert call_args[1]["target"] == "http://example.com"

                results_json = json.loads(call_args[1]["results_json"])
                assert results_json["forms_count"] == 2
                assert results_json["html_length"] == len(html_content)

                meta = call_args[1]["meta"]
                assert meta["count"] == 2
                assert meta["status_code"] == 200
                assert meta["response_size"] == len(html_content)
    finally:
        # Убираем временную директорию
        import shutil

        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def test_api_parse_method_not_allowed():
    """Проверка других методов HTTP"""
    with app.test_client() as client:
        response = client.post("/api/parse")
        assert response.status_code == 405

        response = client.put("/api/parse")
        assert response.status_code == 405

        response = client.delete("/api/parse")
        assert response.status_code == 405


# ==================== Интеграционные тесты ====================


def test_full_integration():
    """Полный интеграционный тест"""
    import tempfile

    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".html", delete=False
    ) as f:
        f.write(
            """
        <html>
            <body>
                <form action="/login" method="post">
                    <input name="username" type="text">
                    <input name="password" type="password">
                </form>
                <form action="/search" method="get">
                    <input name="q" type="search">
                </form>
            </body>
        </html>
        """
        )
        temp_html_path = f.name

    try:
        # Создаем file URL для теста
        if os.name == "nt":
            url_path = temp_html_path.replace("\\", "/")
            test_url = f"file:///{url_path}"
        else:
            test_url = f"file://{temp_html_path}"

        # Создаем временную директорию для тестового файла
        temp_dir = tempfile.mkdtemp()
        test_data_dir = os.path.join(temp_dir, "tests", "test_data")
        os.makedirs(test_data_dir, exist_ok=True)

        try:
            with patch("src.app.save_scan") as mock_save_scan, patch(
                "src.app.save_to_file"
            ) as mock_save_file:

                mock_save_scan.return_value = 100

                with app.test_client() as client:
                    response = client.get(f"/api/parse?url={test_url}")

                    assert response.status_code == 200
                    data = json.loads(response.data)

                    assert data["count"] == 2
                    assert data["scan_id"] == 100
                    assert len(data["forms"]) == 2

                    # Проверяем что формы извлечены
                    assert data["forms"][0]["method"] == "post"
                    assert data["forms"][1]["method"] == "get"
        finally:
            if os.path.exists(temp_dir):
                import shutil

                shutil.rmtree(temp_dir)
    finally:
        os.unlink(temp_html_path)


if __name__ == "__main__":
    tests = [
        # Вспомогательные функции
        test_save_to_file,
        test_save_to_file_unicode,
        test_parse_forms_from_url_success,
        test_parse_forms_from_url_no_html,
        # Flask endpoint
        test_api_parse_missing_url,
        test_api_parse_success,
        test_api_parse_fetch_error,
        test_api_parse_extract_error,
        test_api_parse_file_url,
        test_api_parse_empty_forms,
        test_api_parse_with_encoding,
        test_api_parse_invalid_url_format,
        test_api_parse_save_scan_metadata,
        test_api_parse_method_not_allowed,
        # Интеграционные
        test_full_integration,
    ]

    passed = 0
    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: {e}")

    print(f"\nПройдено: {passed}/{len(tests)}")
