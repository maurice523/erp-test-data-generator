from pydantic import BaseModel
from rapidfuzz import fuzz, process, utils


class GenerateOrdersRequest(BaseModel):
    shipViaCode: str = ""
    orderNo: str = ""
    type: str = ""
    countryCode: str = ""
    minQuantity: str = ""
    maxQuantity: str = ""
    orderCount: str = ""
    minLines: str = ""


def request_to_query_params(request: GenerateOrdersRequest) -> dict[str, object]:

    return {
        "shipViaCode": ship_code_parse(request.shipViaCode),
        "orderNo": request.orderNo,
        "type": type_code_parse(request.type),
        "countryCode": country_code_parse(request.countryCode),
    }


def ship_code_parse(shipViaCode: str) -> str:

    # Specific services map to one code; a bare carrier name maps to a LIKE
    # pattern that matches every service from that carrier.
    ship_codes = {
        'UPS Ground': 'UPS-GND',
        'UPS Next Day Air': 'UPS-NDA',
        'UPS 2nd Day Air': 'UPS-2DAY',
        'UPS 3 Day Select': 'UPS-3DAY',
        'FedEx Ground': 'FDX-GND',
        'FedEx 2Day': 'FDX-2DAY',
        'FedEx Overnight': 'FDX-ONT',
        'USPS Priority Mail': 'USPS-PRI',
        'DHL International Express': 'DHL-INTL',
        'LTL Freight': 'LTL-FRT',
        'Customer Pick Up': 'PICKUP',
        '': '%',
        'UPS': 'UPS-%',
        'FedEx': 'FDX-%',
        'USPS': 'USPS-%',
        'DHL': 'DHL-%',
        'LTL': 'LTL-%',
    }


    shipCodeParsed = shipViaCode.upper()
    
    if shipCodeParsed not in list(ship_codes.values()):
        match_result = process.extractOne(
            shipCodeParsed, 
            ship_codes.keys(), 
            scorer=fuzz.token_sort_ratio,
            processor=utils.default_process,
            score_cutoff=60)
        
        if match_result:
            best_match, _, _ = match_result
            shipCodeParsed = ship_codes.get(best_match)

    return shipCodeParsed



def type_code_parse(order_type: str) -> str:

    type_codes = {
        'No print': 'NO_PRINT',
        'Sample': 'SAMPLE',
    }

    typeCodeParsed = order_type.upper()

    if typeCodeParsed not in list(type_codes.values()):
        match_result = process.extractOne(
            order_type,
            type_codes.keys(),
            scorer=fuzz.token_sort_ratio,
            processor=utils.default_process,
            score_cutoff=60
        )

        if match_result:
            best_match, _, _ = match_result
            typeCodeParsed = type_codes.get(best_match)

    return typeCodeParsed


def country_code_parse(country: str) -> str:

    country_codes = {
        'United States' or 'USA': 'US',
        'Canada': 'CA',
    }

    countryCodeParsed = country.upper()

    if countryCodeParsed not in list(country_codes.values()):
        match_result = process.extractOne(
            country,
            country_codes.keys(),
            scorer=fuzz.token_sort_ratio,
            processor=utils.default_process,
            score_cutoff=60
        )

        if match_result:
            best_match, _, _ = match_result
            countryCodeParsed = country_codes.get(best_match)
    
    return countryCodeParsed
