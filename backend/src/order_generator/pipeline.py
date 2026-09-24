from typing import Any
from baml_client import b

from order_generator.request.request_parse import request_to_query_params
from order_generator.extract.extract_orders import fetch_order_data
from order_generator.analyze.analyze_orders import analyze_orders
from order_generator.generate.generate_orders import generate_orders



def order_generation(
    params: dict[str, object],
    order_count: str,
    min_lines: str = "",
    min_quantity: str = "",
    max_quantity: str = "",
) -> list[dict[str, Any]]:
    dataset, requested_params = fetch_order_data(params)
    analysis_result = analyze_orders(dataset, requested_params)
    generated_orders = generate_orders(
        analysis_result,
        order_count,
        min_lines=min_lines,
        min_quantity=min_quantity,
        max_quantity=max_quantity,
    )
    return generated_orders 


def text_to_orders(text: str) -> list[dict[str, Any]]:
    request = b.ExtractOrderDict(text)
    params = request_to_query_params(request)
    orders = order_generation(
        params=params,
        order_count=request.orderCount,
        min_lines=request.minLines,
        min_quantity=request.minQuantity,
        max_quantity=request.maxQuantity,
    )
    return orders