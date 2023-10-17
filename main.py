from copy import deepcopy
import json
import re
import time
from urllib.request import urlopen


def get_relevant_tags(base_item: dict) -> set[str]:
    tag_list = set()
    for tag in base_item["tags"]:            
        tag_list.add(tag)

    if base_item.get("canHaveInfluence", False):
        tag_list |= {base_item["tags"][0] + suffix for suffix in ["_shaper", "_elder" , "_crusader" , "_basilisk" ,"_eyrie", "_adjudicator"]}

    for child_item in base_item.get("children", []):
        for tag in get_relevant_tags(child_item):
            tag_list.add(tag)
    return tag_list

def apply_format(translation_string, format_list):
    for i in range(len(format_list)):
        if format_list[i] == "+#":
            translation_string = translation_string.replace("{" + str(i) + "}", "+" + "{" + str(i) + "}")
    return translation_string

def translate_stats(stats, domain):
    if domain == "heist_npc":
        translations = heist_stat_translations
    else:
        translations = generic_stat_translations
    translated_strings = []
    unformatted_strings = []
    stat_copy = deepcopy(stats)
    while len(stat_copy) > 0:
        for translation in translations:
            if stat_copy[0]["id"] not in translation["ids"]:
                continue

            translation_stats = [None] * len(translation["ids"])

            for i in range(len(translation["ids"])):
                for stat in stat_copy:
                    if stat["id"] == translation["ids"][i]:
                        translation_stats[i] = stat_copy.pop(stat_copy.index(stat))
                        break
                                    
            for translation_candidate in translation["English"]:
                if condition_is_met(translation_stats, translation_candidate):
                    stat_values = apply_index_handlers(translation_stats, translation_candidate["index_handlers"])
                    formatted_string = apply_format(translation_candidate["string"], translation_candidate["format"])
                    translated_strings.append(formatted_string.format(*stat_values))
                    unformatted_strings.append(formatted_string.format(*["#" for _ in translation_stats]))
                    break
            else:
                # pass
                print("no valid translation found for", translation_stats)
            break
        else:
            # pass
            print("no translation found for", stat_copy.pop(0))
                    
    return translated_strings, unformatted_strings

def apply_index_handlers(stats, index_handlers):
    stat_values = []
    for stat, index_handler in zip(stats, index_handlers):
        if stat is None:
            stat_values.append((None, None))
            continue
        if not index_handler:
            stat_values.append((stat["min"], stat["max"]))
            continue

        match index_handler[0]:
            case "divide_by_one_hundred_2dp_if_required":
                stat_values.append((round(stat["min"] / 100, 2),  round(stat["max"] / 100, 2)))
            case "milliseconds_to_seconds_1dp":
                stat_values.append((round(stat["min"] / 1000, 1), round(stat["max"] / 1000, 1)))
            case "divide_by_twenty":
                stat_values.append((stat["min"] / 20, stat["max"] / 20))
            case "divide_by_one_thousand":
                stat_values.append((stat["min"] / 1000, stat["max"] / 1000))
            case "plus_two_hundred":
                stat_values.append((stat["min"] + 200, stat["max"] + 200))
            case "divide_by_four":
                stat_values.append((stat["min"] / 4, stat["max"] / 4))
            case "milliseconds_to_seconds_2dp":
                stat_values.append((round(stat["min"] / 1000, 2), round(stat["max"] / 1000, 2)))
            case "divide_by_ten_0dp":
                stat_values.append((round(stat["min"] / 10), round(stat["max"] / 10)))
            case "divide_by_fifteen_0dp":
                stat_values.append((round(stat["min"] / 15), round(stat["max"] / 15)))
            case "divide_by_six":
                stat_values.append((stat["min"] / 6, stat["max"] / 6))
            case "per_minute_to_per_second_2dp_if_required":
                stat_values.append((round(stat["min"] / 60, 2), round(stat["max"] / 60, 2)))
            case "divide_by_three":
                stat_values.append((stat["min"] / 3, stat["max"] / 3))
            case "per_minute_to_per_second_2dp":
                stat_values.append((round(stat["min"] / 60, 2), round(stat["max"] / 60, 2)))
            case "per_minute_to_per_second_1dp":
                stat_values.append((round(stat["min"] / 60, 1), round(stat["max"] / 60, 1)))
            case "divide_by_one_hundred_2dp":
                stat_values.append((round(stat["min"] / 100, 2), round(stat["max"] / 100, 2)))
            case "divide_by_one_hundred":
                stat_values.append((stat["min"] / 100, stat["max"] / 100))
            case "divide_by_two_0dp":
                stat_values.append((round(stat["min"] / 2), round(stat["max"] / 2)))
            case "double":
                stat_values.append((stat["min"] * 2, stat["max"] * 2))
            case "negate":
                stat_values.append((-stat["min"], -stat["max"]))
            case "divide_by_ten_1dp":
                stat_values.append((round(stat["min"] / 10, 1), round(stat["max"] / 10, 1)))
            case "deciseconds_to_seconds":
                stat_values.append((stat["min"] / 10, stat["max"] / 10))
            case "60%_of_value":
                stat_values.append((stat["min"] * 0.6, stat["max"] * 0.6))
            case "divide_by_twenty_then_double_0dp":
                stat_values.append((round(stat["min"] / 20) * 2, round(stat["max"] / 20) * 2))
            case "divide_by_fifty":
                stat_values.append((stat["min"] / 50, stat["max"] / 50))
            case "divide_by_five":
                stat_values.append((stat["min"] / 5, stat["max"] / 5))
            case "30%_of_value":
                stat_values.append((stat["min"] * 0.3, stat["max"] * 0.3))
            case "milliseconds_to_seconds":
                stat_values.append((stat["min"] / 1000, stat["max"] / 1000))
            case "negate_and_double":
                stat_values.append((-stat["min"] * 2, -stat["max"] * 2))
            case _:
                stat_values.append((stat["min"], stat["max"]))

    return ["({}-{})".format(values[0], values[1]) if values[0] != values[1] else values[0] for values in stat_values]


def condition_is_met(translation_stats, translation_candidate):
    for stat, condition in zip(translation_stats, translation_candidate["condition"]):
        if stat is None:
            continue
        if "min" in  condition and stat["min"] < condition["min"]:
            return False
        if "max" in  condition and stat["max"] > condition["max"]:
            return False
    return True


def filter_for_relevant_mods(mods: dict, base_items: list):
    tag_list = set()
    domain_list = set()
    for base_item in base_items:
        tag_list |= get_relevant_tags(base_item)
        domain_list.add(base_item["domain"])

    relevant_mods = {domain: {} for domain in domain_list}
    for mod_name, mod in mods.items():
        if mod["domain"] not in domain_list or mod["generation_type"] not in ["prefix", "suffix"] or "royale" in mod_name.lower():
            continue
        for weight in mod["spawn_weights"]:
            if weight["tag"] in tag_list:
                relevant_mods[mod["domain"]][mod_name] = mod
                break
    return relevant_mods


def add_translations(mods: dict):
    for domain, mod_list in mods.items():
        for mod in mod_list.values():
            translated_strings, unformatted_strings = translate_stats(mod["stats"], domain)
            mod["translated_strings"] = translated_strings
            mod["unformatted_strings"] = unformatted_strings

    return mods

def add_tiers(mods: dict):
    tier_groups = {}
    for mod_list in mods.values():
        for mod_name, mod in mod_list.items():
            if "elevated" in mod["name"].lower():
                mod["tier"] = 0
                continue
            mod_number = re.search(r"\d+", mod_name)
            if mod_number is None:
                mod["tier"] = 1
                continue
            mod["temp_number"] = int(mod_number.group()[0])
            if mod["type"] not in tier_groups:
                tier_groups[mod["type"]] = []
            tier_groups[mod["type"]].append(mod["temp_number"])

    for mod_list in mods.values():
        for mod_name, mod in mod_list.items():
            if "tier" in mod:
                continue
            mod_number = mod.pop("temp_number")
            mod["tier"] = max(tier_groups[mod["type"]]) + min(tier_groups[mod["type"]]) - int(mod_number)


if __name__ == "__main__":
    start_time = time.time()
    response = urlopen("https://raw.githubusercontent.com/Liberatorist/RePoE/master/RePoE/data/mods.min.json")
    mods = json.loads(response.read())

    response = urlopen("https://raw.githubusercontent.com/Liberatorist/RePoE/master/RePoE/data/stat_translations.min.json")
    generic_stat_translations = json.loads(response.read())

    response = urlopen("https://raw.githubusercontent.com/Liberatorist/RePoE/master/RePoE/data/stat_translations/heist_equipment.min.json")
    heist_stat_translations = json.loads(response.read())

    with open("crafting-data/items.json") as f:
        base_items = json.load(f)

    relevant_mods = filter_for_relevant_mods(mods, base_items)
    add_tiers(relevant_mods)
    add_translations(relevant_mods)
    print("time taken:", time.time() - start_time)
    with open("crafting-data/mods.json", "w") as f:
        json.dump(relevant_mods, f, indent=2)
    with open("crafting-data/mods.min.json", "w") as f:
        json.dump(relevant_mods, f, separators=(",", ":"))