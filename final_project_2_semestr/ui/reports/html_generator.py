import json
from pathlib import Path
from datetime import datetime
from typing import Any


class HtmlReportGenerator:
    """Генератор HTML-отчётов о тестировании."""

    def __init__(self, output_dir: str = "./reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        algo_name: str,
        results: list[dict[str, Any]],
        total_tested: int,
        passed: int,
        failed: int,
        avg_error: float,
    ) -> str:
        """
        Генерация HTML-отчёта.

        Returns:
            str: путь к сгенерированному файлу
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{algo_name.replace(' ', '_')}_{timestamp}.html"
        filepath = self.output_dir / filename

        pass_rate = (passed / max(total_tested, 1)) * 100

        # Генерация строк таблицы
        table_rows = ""
        for r in results:
            target_str = str(r["target"]) if r["target"] is not None else "—"
            pred_str = str(r["predicted"]) if r["predicted"] is not None else "—"
            error_str = f"{r['error_pct']:.1f}%" if r["error_pct"] is not None else "—"

            row_class = ""
            if r.get("passed"):
                row_class = "passed"
            elif r.get("predicted") is not None:
                row_class = "failed"

            table_rows += f"""
            <tr class="{row_class}">
                <td>{r['filename']}</td>
                <td>{target_str}</td>
                <td>{pred_str}</td>
                <td>{error_str}</td>
                <td>{r['time']:.2f} с</td>
                <td>{r['status']}</td>
            </tr>"""

        # Сводка в JSON (для визуализации через JS)
        chart_data = json.dumps({
            "passed": passed,
            "failed": failed,
            "pass_rate": round(pass_rate, 1),
            "avg_error": round(avg_error, 2),
            "results": [
                {
                    "filename": r["filename"],
                    "error_pct": r["error_pct"],
                    "passed": r.get("passed", False),
                }
                for r in results
            ]
        })

        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Отчёт тестирования — {algo_name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        .summary {{
            display: flex;
            gap: 20px;
            margin: 20px 0;
            flex-wrap: wrap;
        }}
        .summary-card {{
            flex: 1;
            min-width: 150px;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            color: white;
            font-weight: bold;
        }}
        .card-total {{ background: #2196F3; }}
        .card-passed {{ background: #4CAF50; }}
        .card-failed {{ background: #f44336; }}
        .card-error {{ background: #FF9800; }}
        .summary-card .value {{ font-size: 32px; }}
        .summary-card .label {{ font-size: 14px; opacity: 0.9; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background: #333;
            color: white;
            padding: 10px;
            text-align: left;
        }}
        td {{ padding: 8px 10px; border-bottom: 1px solid #ddd; }}
        tr.passed {{ background: #e8f5e9; }}
        tr.failed {{ background: #ffebee; }}
        .footer {{
            margin-top: 30px;
            color: #666;
            font-size: 12px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Отчёт тестирования</h1>
        <p><strong>Алгоритм:</strong> {algo_name}</p>
        <p><strong>Дата:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>

        <div class="summary">
            <div class="summary-card card-total">
                <div class="value">{total_tested}</div>
                <div class="label">Всего изображений</div>
            </div>
            <div class="summary-card card-passed">
                <div class="value">{passed}</div>
                <div class="label">Пройдено (&le;10%)</div>
            </div>
            <div class="summary-card card-failed">
                <div class="value">{failed}</div>
                <div class="label">Провалено</div>
            </div>
            <div class="summary-card card-error">
                <div class="value">{pass_rate:.1f}%</div>
                <div class="label">Процент успеха</div>
            </div>
        </div>

        <p>Средняя погрешность: <strong>{avg_error:.2f}%</strong></p>

        <h2>Детальные результаты</h2>
        <table>
            <thead>
                <tr>
                    <th>Файл</th>
                    <th>Эталон</th>
                    <th>Найдено</th>
                    <th>Погрешность</th>
                    <th>Время</th>
                    <th>Статус</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>

        <div class="footer">
            Система подсчёта клеток на гистологических изображениях &copy; 2025
        </div>
    </div>
</body>
</html>"""

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

        return str(filepath)