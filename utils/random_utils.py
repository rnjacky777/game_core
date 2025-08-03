import random
from typing import List, Tuple, TypeVar, Optional

T = TypeVar('T')

def weighted_choice(choices: List[Tuple[T, float]]) -> Optional[T]:
    """
    從一個 (物件, 權重) 的列表中，根據權重隨機選擇一個物件。

    Args:
        choices: 一個包含 (物件, 權重) 元組的列表。權重應為數字。

    Returns:
        根據權重隨機選中的物件。如果列表為空或所有權重都小於等於0，則返回 None。
    """
    if not choices:
        return None

    # 過濾掉權重不為正的選項
    valid_choices = [(item, weight) for item, weight in choices if weight > 0]
    if not valid_choices:
        return None

    total_weight = sum(weight for _, weight in valid_choices)
    r = random.uniform(0, total_weight)

    upto = 0
    for item, weight in valid_choices:
        if upto + weight >= r:
            return item
        upto += weight

    # 理論上不應該執行到這裡，但作為保險，回傳最後一個有效項目
    return valid_choices[-1][0]

