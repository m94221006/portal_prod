
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def monitor_in_region(monitorlist,region_name):
    datalist =[monitor for monitor in monitorlist if monitor.region_name== region_name]
    return datalist

@register.filter
def region_in_count(monitorlist,region_name):
    itemlist = list([monitor for monitor in monitorlist if monitor.region_name == region_name])
    return len(itemlist)

@register.filter
def instance_in_region(instancelist,region_name):
    datalist =[instance for instance in instancelist if instance.region_name == region_name]
    return datalist

@register.filter
def instance_region_in_count(instancelist,region_name):
    itemlist = list([instance for instance in instancelist if instance.region_name == region_name])
    return len(itemlist)

@register.filter
def return_item(monitor, i):
    try:
        if i==100:
            if monitor.i_vip == True: return 'special'
        elif i ==101:
            if monitor.i_vip == True: return 'selected'
            return ''
        return item[i]
    except:
        return None

@register.filter
def replace_tobr(value,pattern):
    return mark_safe(value.replace(pattern,"<br/>"))

    