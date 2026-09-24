class OrderDict {
    shipViaCode string @description("shipping carrier")  
    orderNo string @description("order number")
    type string @description("order type")
    countryCode string @description("country")
    minQuantity string @description("minimum quantity for each generated order line")
    maxQuantity string @description("maximum quantity for each generated order line")
    orderCount string @description("number of orders")
    minLines string @description("minimum number of lines per generated order")
}

function ExtractOrderDict(text: string) -> OrderDict {
    client CustomGPT5Nano
    prompt #"
        From the following statement extract carrier, order number, 
        order type (current are sample and no print), country, minimum and maximum
        line quantity, number of orders,
        and the minimum number of lines per generated order.
        If the information is not present return "" for that field. 
        If it is not present dont make it up:

        {{ text }}
        {{ ctx.output_format }}
    "#

}
