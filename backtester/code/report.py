from __future__ import annotations


def format_currency(value: float) -> str:
    return f"${value:,.2f}"


def format_percent(value: float) -> str:
    return f"{value * 100:,.2f}%"


def render_yearly_performance(rows: list[dict]) -> str:
    headers = ["year", "end_value", "return", "mdd", "BM value", "BM return", "BM mdd"]
    matrix = [headers]
    for row in rows:
        matrix.append(
            [
                str(row["year"]),
                format_currency(float(row["end_value"])),
                format_percent(float(row["return"])),
                format_percent(float(row["mdd"])),
                format_currency(float(row["bm_value"])),
                format_percent(float(row["bm_return"])),
                format_percent(float(row["bm_mdd"])),
            ]
        )

    widths = [max(len(item[column]) for item in matrix) for column in range(len(headers))]
    lines = ["Yearly Performance"]
    for row_index, row in enumerate(matrix):
        padded = [row[column].rjust(widths[column]) for column in range(len(headers))]
        lines.append(" | ".join(padded))
        if row_index == 0:
            lines.append("-+-".join("-" * width for width in widths))
    return "\n".join(lines)


def render_final_performance(summary: dict) -> str:
    lines = [
        "Final Performance",
        f"period:               {summary['start_date']} -> {summary['end_date']}",
        f"ending_value:         {format_currency(float(summary['ending_value']))}",
        f"cumulative_return:    {format_percent(float(summary['cumulative_return']))}",
        f"CAGR:                 {format_percent(float(summary['cagr']))}",
        f"overall_MDD:          {format_percent(float(summary['overall_mdd']))}",
        f"average_holding_days: {float(summary['average_holding_days']):.1f}",
        "",
        f"benchmark_ending:     {format_currency(float(summary['benchmark_ending_value']))}",
        f"benchmark_return:     {format_percent(float(summary['benchmark_cumulative_return']))}",
        f"benchmark_CAGR:       {format_percent(float(summary['benchmark_cagr']))}",
        f"benchmark_MDD:        {format_percent(float(summary['benchmark_overall_mdd']))}",
        f"total_principal:      {format_currency(float(summary['total_contributed_capital']))}",
    ]
    return "\n".join(lines)
