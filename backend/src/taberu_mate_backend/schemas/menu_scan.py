# ruff: noqa: E501,RUF001
import json
from typing import Any, cast

MENU_SCAN_RESPONSE_FORMAT = cast(
    dict[str, Any],
    json.loads(
        """
        {
          "name": "scan_order_menu",
          "strict": true,
          "schema": {
            "type": "object",
            "$comment": "扫码点餐菜单识别结果的根对象",
            "description": "Structured menu data extracted from menu images for QR-code ordering systems.",
            "required": ["menu", "categories", "items"],
            "additionalProperties": false,
            "properties": {
              "menu": {
                "type": "object",
                "$comment": "菜单整体信息",
                "description": "General information about the recognized menu.",
                "required": [
                  "source_language",
                  "target_language",
                  "currency",
                  "restaurant_name_original",
                  "restaurant_name_translated"
                ],
                "additionalProperties": false,
                "properties": {
                  "source_language": {
                    "type": "string",
                    "$comment": "原始菜单语言",
                    "description": "The original language code of the menu, such as zh-CN, ja, en, or ko."
                  },
                  "target_language": {
                    "type": "string",
                    "$comment": "翻译目标语言",
                    "description": "The target language code used for translated fields."
                  },
                  "currency": {
                    "type": "string",
                    "$comment": "菜单价格币种",
                    "description": "The currency code used by menu prices, such as CNY, JPY, USD, or EUR."
                  },
                  "restaurant_name_original": {
                    "type": ["string", "null"],
                    "$comment": "餐厅原名",
                    "description": "The restaurant name in the original language, if visible."
                  },
                  "restaurant_name_translated": {
                    "type": ["string", "null"],
                    "$comment": "餐厅译名",
                    "description": "The translated restaurant name, if available."
                  }
                }
              },
              "categories": {
                "type": "array",
                "$comment": "菜单分类列表，可包含饮品、主食、甜品、限定、套餐等多种分类",
                "description": "A list of menu categories used for display, grouping, and filtering.",
                "items": {
                  "type": "object",
                  "required": [
                    "id",
                    "parent_id",
                    "name_original",
                    "name_translated",
                    "type",
                    "sort_order"
                  ],
                  "additionalProperties": false,
                  "properties": {
                    "id": {
                      "type": "string",
                      "$comment": "分类唯一 ID",
                      "description": "A unique category identifier."
                    },
                    "parent_id": {
                      "type": ["string", "null"],
                      "$comment": "父级分类 ID，没有则为 null",
                      "description": "The parent category ID for nested categories, or null for top-level categories."
                    },
                    "name_original": {
                      "type": "string",
                      "$comment": "分类原名",
                      "description": "The category name in the original menu language."
                    },
                    "name_translated": {
                      "type": "string",
                      "$comment": "分类译名",
                      "description": "The translated category name."
                    },
                    "type": {
                      "type": "string",
                      "$comment": "分类类型，用于前端筛选和图标展示",
                      "description": "The normalized category type.",
                      "enum": [
                        "staple_food",
                        "main_dish",
                        "side_dish",
                        "snack",
                        "dessert",
                        "drink",
                        "tea",
                        "coffee",
                        "alcohol",
                        "set_meal",
                        "combo",
                        "soup",
                        "noodle",
                        "rice",
                        "bbq",
                        "hot_pot",
                        "seafood",
                        "vegetarian",
                        "kids",
                        "seasonal",
                        "limited",
                        "recommended",
                        "series",
                        "other"
                      ]
                    },
                    "sort_order": {
                      "type": "integer",
                      "$comment": "分类排序",
                      "description": "The display order of the category."
                    }
                  }
                }
              },
              "items": {
                "type": "array",
                "$comment": "菜品列表",
                "description": "A list of recognized menu items.",
                "items": {
                  "type": "object",
                  "required": [
                    "id",
                    "primary_category_id",
                    "category_ids",
                    "name_original",
                    "name_translated",
                    "description_original",
                    "description_translated",
                    "price",
                    "item_type",
                    "tags",
                    "taste_profile",
                    "allergens",
                    "dietary",
                    "options",
                    "availability",
                    "confidence"
                  ],
                  "additionalProperties": false,
                  "properties": {
                    "id": {
                      "type": "string",
                      "$comment": "菜品唯一 ID",
                      "description": "A unique menu item identifier."
                    },
                    "primary_category_id": {
                      "type": "string",
                      "$comment": "主要展示分类 ID",
                      "description": "The primary category used for main menu display."
                    },
                    "category_ids": {
                      "type": "array",
                      "$comment": "该菜品所属的多个分类 ID",
                      "description": "All category IDs associated with this item.",
                      "items": {
                        "type": "string"
                      }
                    },
                    "name_original": {
                      "type": "string",
                      "$comment": "菜品原名",
                      "description": "The item name in the original menu language."
                    },
                    "name_translated": {
                      "type": "string",
                      "$comment": "菜品译名",
                      "description": "The translated item name."
                    },
                    "description_original": {
                      "type": ["string", "null"],
                      "$comment": "原始描述",
                      "description": "The original item description, if visible."
                    },
                    "description_translated": {
                      "type": ["string", "null"],
                      "$comment": "翻译后的描述",
                      "description": "The translated item description, if available."
                    },
                    "price": {
                      "type": "object",
                      "$comment": "价格信息",
                      "description": "Price information for the item.",
                      "required": ["amount", "currency", "raw_text"],
                      "additionalProperties": false,
                      "properties": {
                        "amount": {
                          "type": ["number", "null"],
                          "$comment": "数值价格",
                          "description": "The numeric price amount, or null if not recognized."
                        },
                        "currency": {
                          "type": "string",
                          "$comment": "币种",
                          "description": "The currency code for the price."
                        },
                        "raw_text": {
                          "type": ["string", "null"],
                          "$comment": "菜单上识别到的原始价格文本",
                          "description": "The raw price text recognized from the menu image."
                        }
                      }
                    },
                    "item_type": {
                      "type": "string",
                      "$comment": "菜品标准类型",
                      "description": "The normalized item type.",
                      "enum": [
                        "food",
                        "drink",
                        "dessert",
                        "set_meal",
                        "add_on",
                        "sauce",
                        "other"
                      ]
                    },
                    "tags": {
                      "type": "array",
                      "$comment": "菜品标签，用于前端筛选",
                      "description": "Display and filtering tags for the item.",
                      "items": {
                        "type": "string",
                        "enum": [
                          "recommended",
                          "signature",
                          "popular",
                          "new",
                          "limited",
                          "seasonal",
                          "spicy",
                          "sweet",
                          "cold",
                          "hot",
                          "iced",
                          "vegetarian",
                          "vegan",
                          "kids_friendly",
                          "large_portion",
                          "small_portion"
                        ]
                      }
                    },
                    "taste_profile": {
                      "type": "object",
                      "$comment": "味型信息，0 到 5 表示强度",
                      "description": "Taste intensity profile from 0 to 5.",
                      "required": [
                        "spicy_level",
                        "sweet_level",
                        "salty_level",
                        "sour_level",
                        "bitter_level",
                        "richness_level"
                      ],
                      "additionalProperties": false,
                      "properties": {
                        "spicy_level": {
                          "type": "integer",
                          "minimum": 0,
                          "maximum": 5,
                          "$comment": "辣度",
                          "description": "Spiciness level from 0 to 5."
                        },
                        "sweet_level": {
                          "type": "integer",
                          "minimum": 0,
                          "maximum": 5,
                          "$comment": "甜度",
                          "description": "Sweetness level from 0 to 5."
                        },
                        "salty_level": {
                          "type": "integer",
                          "minimum": 0,
                          "maximum": 5,
                          "$comment": "咸度",
                          "description": "Saltiness level from 0 to 5."
                        },
                        "sour_level": {
                          "type": "integer",
                          "minimum": 0,
                          "maximum": 5,
                          "$comment": "酸度",
                          "description": "Sourness level from 0 to 5."
                        },
                        "bitter_level": {
                          "type": "integer",
                          "minimum": 0,
                          "maximum": 5,
                          "$comment": "苦味程度",
                          "description": "Bitterness level from 0 to 5."
                        },
                        "richness_level": {
                          "type": "integer",
                          "minimum": 0,
                          "maximum": 5,
                          "$comment": "浓郁或油润程度",
                          "description": "Richness or heaviness level from 0 to 5."
                        }
                      }
                    },
                    "allergens": {
                      "type": "array",
                      "$comment": "可能致敏因素",
                      "description": "Possible allergen factors detected or inferred from the menu.",
                      "items": {
                        "type": "string",
                        "enum": [
                          "gluten",
                          "crustaceans",
                          "eggs",
                          "fish",
                          "peanuts",
                          "soybeans",
                          "milk",
                          "tree_nuts",
                          "celery",
                          "mustard",
                          "sesame",
                          "sulfites",
                          "lupin",
                          "molluscs",
                          "alcohol",
                          "unknown"
                        ]
                      }
                    },
                    "dietary": {
                      "type": "object",
                      "$comment": "饮食禁忌和饮食类型信息",
                      "description": "Dietary and restriction information.",
                      "required": [
                        "vegetarian",
                        "vegan",
                        "halal",
                        "contains_pork",
                        "contains_beef",
                        "contains_chicken",
                        "contains_seafood",
                        "contains_alcohol"
                      ],
                      "additionalProperties": false,
                      "properties": {
                        "vegetarian": {
                          "type": ["boolean", "null"],
                          "$comment": "是否素食",
                          "description": "Whether the item is vegetarian, or null if uncertain."
                        },
                        "vegan": {
                          "type": ["boolean", "null"],
                          "$comment": "是否纯素",
                          "description": "Whether the item is vegan, or null if uncertain."
                        },
                        "halal": {
                          "type": ["boolean", "null"],
                          "$comment": "是否清真",
                          "description": "Whether the item appears halal, or null if uncertain."
                        },
                        "contains_pork": {
                          "type": ["boolean", "null"],
                          "$comment": "是否含猪肉",
                          "description": "Whether the item contains pork, or null if uncertain."
                        },
                        "contains_beef": {
                          "type": ["boolean", "null"],
                          "$comment": "是否含牛肉",
                          "description": "Whether the item contains beef, or null if uncertain."
                        },
                        "contains_chicken": {
                          "type": ["boolean", "null"],
                          "$comment": "是否含鸡肉",
                          "description": "Whether the item contains chicken, or null if uncertain."
                        },
                        "contains_seafood": {
                          "type": ["boolean", "null"],
                          "$comment": "是否含海鲜",
                          "description": "Whether the item contains seafood, or null if uncertain."
                        },
                        "contains_alcohol": {
                          "type": ["boolean", "null"],
                          "$comment": "是否含酒精",
                          "description": "Whether the item contains alcohol, or null if uncertain."
                        }
                      }
                    },
                    "options": {
                      "type": "array",
                      "$comment": "规格、加料、甜度、冰度、冷热等选项",
                      "description": "Selectable item options such as size, toppings, temperature, sweetness, or ice level.",
                      "items": {
                        "type": "object",
                        "required": [
                          "id",
                          "name_original",
                          "name_translated",
                          "required",
                          "min_select",
                          "max_select",
                          "choices"
                        ],
                        "additionalProperties": false,
                        "properties": {
                          "id": {
                            "type": "string",
                            "$comment": "选项组 ID",
                            "description": "A unique option group identifier."
                          },
                          "name_original": {
                            "type": "string",
                            "$comment": "选项组原名",
                            "description": "The option group name in the original language."
                          },
                          "name_translated": {
                            "type": "string",
                            "$comment": "选项组译名",
                            "description": "The translated option group name."
                          },
                          "required": {
                            "type": "boolean",
                            "$comment": "是否必选",
                            "description": "Whether the customer must select from this option group."
                          },
                          "min_select": {
                            "type": "integer",
                            "$comment": "最少选择数量",
                            "description": "The minimum number of choices required."
                          },
                          "max_select": {
                            "type": "integer",
                            "$comment": "最多选择数量",
                            "description": "The maximum number of choices allowed."
                          },
                          "choices": {
                            "type": "array",
                            "$comment": "具体选项列表",
                            "description": "Available choices in this option group.",
                            "items": {
                              "type": "object",
                              "required": [
                                "id",
                                "name_original",
                                "name_translated",
                                "extra_price"
                              ],
                              "additionalProperties": false,
                              "properties": {
                                "id": {
                                  "type": "string",
                                  "$comment": "选项 ID",
                                  "description": "A unique choice identifier."
                                },
                                "name_original": {
                                  "type": "string",
                                  "$comment": "选项原名",
                                  "description": "The choice name in the original language."
                                },
                                "name_translated": {
                                  "type": "string",
                                  "$comment": "选项译名",
                                  "description": "The translated choice name."
                                },
                                "extra_price": {
                                  "type": "number",
                                  "$comment": "额外价格",
                                  "description": "The additional price for this choice."
                                }
                              }
                            }
                          }
                        }
                      }
                    },
                    "availability": {
                      "type": "object",
                      "$comment": "售卖状态",
                      "description": "Availability status of the item.",
                      "required": ["status", "note"],
                      "additionalProperties": false,
                      "properties": {
                        "status": {
                          "type": "string",
                          "$comment": "当前状态",
                          "description": "The current availability status.",
                          "enum": ["available", "sold_out", "limited", "unknown"]
                        },
                        "note": {
                          "type": ["string", "null"],
                          "$comment": "状态备注",
                          "description": "Additional availability notes, if any."
                        }
                      }
                    },
                    "confidence": {
                      "type": "object",
                      "$comment": "AI 识别置信度",
                      "description": "Confidence scores for extraction, translation, classification, and allergen inference.",
                      "required": [
                        "ocr",
                        "translation",
                        "classification",
                        "price_detection",
                        "allergen_detection"
                      ],
                      "additionalProperties": false,
                      "properties": {
                        "ocr": {
                          "type": "number",
                          "minimum": 0,
                          "maximum": 1,
                          "$comment": "OCR 识别置信度",
                          "description": "Confidence score for OCR extraction."
                        },
                        "translation": {
                          "type": "number",
                          "minimum": 0,
                          "maximum": 1,
                          "$comment": "翻译置信度",
                          "description": "Confidence score for translation quality."
                        },
                        "classification": {
                          "type": "number",
                          "minimum": 0,
                          "maximum": 1,
                          "$comment": "分类置信度",
                          "description": "Confidence score for category and item type classification."
                        },
                        "price_detection": {
                          "type": "number",
                          "minimum": 0,
                          "maximum": 1,
                          "$comment": "价格识别置信度",
                          "description": "Confidence score for price detection."
                        },
                        "allergen_detection": {
                          "type": "number",
                          "minimum": 0,
                          "maximum": 1,
                          "$comment": "过敏原推断置信度",
                          "description": "Confidence score for allergen detection or inference."
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
    ),
)
