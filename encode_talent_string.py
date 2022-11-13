from blizz_spec_ids import blizz_spec_ids
from nodes import nodes
from node_orders import node_orders
import ExportDataStream

def encode_talent_string(selected_talents, spec_name):
    export_string = ExportDataStream.ExportDataStream()

    export_string.AddValue(8, 1)
    export_string.AddValue(16, blizz_spec_ids[spec_name])
    export_string.AddValue(128, 0)

    node_order = node_orders[spec_name]

    for n in node_order:
        if n in nodes[spec_name]:
            this_node = nodes[spec_name][n]
        else:
            # if a node isn't found, that means it's from another spec
            # since it's from another spec, we know it is not selected
            export_string.AddValue(1, 0) # this node is not selected
            continue
    
        tids = []
        max_ranks = []
        for k in this_node["entries"]:
            tids += [k["id"]]
            max_ranks += [k["maxRanks"]]

        match = False
        points = 0
        which_node = 0
        for i, tid in enumerate(tids):
            if tid in selected_talents:
                match = True
                which_choice = i
                points = selected_talents[tid]

        # from https://github.com/tomrus88/BlizzardInterfaceCode/blob/408c91e884de3ec76545550a19150619bd57378d/Interface/AddOns/Blizzard_ClassTalentUI/Blizzard_ClassTalentImportExport.lua

        # -- Is Node Selected, 1 bit.
        # -- Specifies if the node is selected in the loadout. If it is unselected, the 0 bit is the only information written for that node, and the next bit in the stream will contain the selected value for the next node in the tree. 

        if match == False:
            export_string.AddValue(1, 0) # this node is not selected
            continue

        if "freeNode" in this_node:
            export_string.AddValue(1, 0) # free nodes are NOT selected
            continue
    
        # the node is selected
        export_string.AddValue(1, 1)
    
        # -- Is Partially Ranked, 1 bit.
        # -- (Only written if isNodeSelected is true). Indicates if the node is partially ranked.  For example, if a node has 3 ranks, and the player only puts 2 ranks into that node, it is marked as partially ranked and the number of ranks is written to the stream.  If it is not partially ranked, the max number of ranks is assumed.

        # -- Ranks Purchased, 6 bits.
        # -- (Only written if IsPartiallyRanked is true). The number of ranks a player put into this node, between 1 (inclusive) and max ranks for that node (exclusive).

        if points < max_ranks[0]:
            export_string.AddValue(1, 1) # yes, partially ranked
            export_string.AddValue(6, points) # the number of ranks
        else:
            export_string.AddValue(1, 0) # no, not partially ranked
            
        # -- Is Choice Node, 1 bit
        # -- (Only written if isNodeSelected is true). Specifies if this node is a choice node, where a player must choose one out of the available options.

        # -- Choice Entry Index, 2 bits.
        # -- (Only written if isChoiceNode is true). The index of selected entry for the choice node. Zero-based index (first entry is index 0).
            
        if this_node["type"] == "choice":
            export_string.AddValue(1, 1) # yes, a choice node
            export_string.AddValue(2, which_choice) # which choice node
        else:
            export_string.AddValue(1, 0) # no, not a choice node

    return export_string.GetExportString()

