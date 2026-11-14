from django import template

register = template.Library()

@register.filter
def get_obj_attr(obj, attr):
    return getattr(obj, attr)

@register.filter
def percent(share, places = 0):
    # 0.534 -> "53%"; None -> "-".
    if share == None:
        return "-"
    return ("{:." + str(int(places)) + "f}%").format(share * 100)


@register.filter
def signed(value, places = 1):
    # 12.3 -> "+12.3", -4 -> "-4.0"; None -> "-".
    if value == None:
        return "-"
    return ("{:+." + str(int(places)) + "f}").format(value)
