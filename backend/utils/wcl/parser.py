import logging
import operator


def wcl_parse(
    rankings,
    extractor,
    is_sorted=True,
    is_aggregated=True,
    only_use_ids=False,
    flatten=False,
):
    from backend.utils.wcl.utils import wcl_top10

    groupings = {}
    map_name_id_icon = []
    metadata = {}

    # go through each element in rankings
    # and use extractor to pull out what we want to focus on
    # and then add it to groupings
    # also, build out a map of name to -> id icon for each element
    for k in rankings:
        # extractor pulls out the elements we want to use
        names_in_set, name_id_icons = extractor(k)
        map_name_id_icon += name_id_icons

        # df prepatch: skip logs with broken talents
        if "talents" in k:
            if len(k["talents"]) < 10:
                continue

        add_this = None
        if flatten:  # use each element of names_in_set separately
            added_this_round = []
            for element in names_in_set:
                add_this = tuple([element])
                if add_this not in groupings:
                    groupings[add_this] = 0
                    metadata[add_this] = []
                if add_this not in added_this_round:
                    groupings[add_this] += 1
                    added_this_round += [add_this]

        else:  # treat the elements in aggregate; don't consider them individually
            if is_sorted:
                add_this = tuple(sorted(names_in_set))
            else:
                add_this = tuple(names_in_set)

            if add_this not in groupings:
                groupings[add_this] = 0
                metadata[add_this] = []

            groupings[add_this] += 1

        if add_this == None:
            continue

        link_text = ""
        sort_value = 0

        # is this for m+ or raid?
        if "keystoneLevel" in k:  # m+
            link_text = "+%d" % k["keystoneLevel"]
            sort_value = int(k["keystoneLevel"])
        elif "total" in k:  # raid
            link_text = "%.2fk" % (float(k["total"]) / 1000)
            sort_value = float(k["total"]) / 1000

        # 0 is an artifact of band value, for aggregated reports in the popover -- unused now
        report_id = ""
        fight_id = 0
        if "reportID" in k:
            report_id = k["reportID"]
            if "fightID" in k:
                fight_id = k["fightID"]
            else:
                logging.info("no fight ID found!")

        if flatten:
            for element in names_in_set:
                add_this = tuple([element])
                metadata[add_this] += [[sort_value, 0, link_text, report_id, fight_id]]
        else:
            metadata[add_this] += [[sort_value, 0, link_text, report_id, fight_id]]

    # get rid of duplicate icons in the look up table / mapping
    no_duplicate_mapping = {}
    for mapping in map_name_id_icon:
        if "id" not in mapping:
            logging.info(mapping)
            logging.info(extractor)
            continue
        if only_use_ids:
            no_duplicate_mapping[mapping["id"]] = [mapping["id"], ""]
        else:
            no_duplicate_mapping[mapping["id"]] = [
                mapping["id"],
                mapping["icon"],
                mapping["name"],
            ]

    for k, v in metadata.items():
        metadata[k] = sorted(v, key=operator.itemgetter(0), reverse=True)[
            :1
        ]  # just the best one

    return wcl_top10(groupings, metadata), no_duplicate_mapping
