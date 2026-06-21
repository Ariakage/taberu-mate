# Menu Scan API

菜单识别接口用于让前端上传菜单图片，并指定需要输出的语言。后端会把图片传给 LLM，并强制要求模型按内置的 `scan_order_menu` JSON Schema 返回结果。

## Endpoint

```http
POST /api/v1/menus/scan
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

调用这个 API 前，用户必须先登录，并在请求头里带上登录接口返回的 `access_token`。

前端默认使用流式接口：

```http
POST /api/v1/menus/scan/stream
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
Accept: text/event-stream
```

流式接口会返回 SSE 事件：

```text
event: status
data: {"message":"图片已上传, 正在识别菜单..."}

event: delta
data: {"content":"{\"menu\""}

event: done
data: {"content":"{\"menu\":{...},\"categories\":[...],\"items\":[...]}"}

event: error
data: {"message":"stream error: stream ID 1; INTERNAL_ERROR; received from peer (internal_server_error)"}
```

非流式接口仍然保留，适合 curl 或后端集成测试；流式接口适合浏览器前端，能更早收到状态和模型增量内容。

## Form Data

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `image` | file | 是 | 菜单图片。支持 `image/jpeg`、`image/png`、`image/webp`，最大 10 MB。 |
| `target_language` | string | 是 | 输出语言，可以传语言代码或语言名，例如 `zh-CN`、`en`、`ja`、`Chinese`。 |
| `model` | string | 否 | 临时覆盖 `.env` 里的 `TABERU_MATE_AI_MODEL`。 |
| `prompt` | string | 否 | 临时覆盖默认菜单识别提示词。通常不需要传。 |

## cURL

```bash
curl -X POST http://127.0.0.1:8000/api/v1/menus/scan \
  -H "Authorization: Bearer <access_token>" \
  -F "target_language=zh-CN" \
  -F "image=@/absolute/path/to/menu.jpg;type=image/jpeg"
```

带模型覆盖：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/menus/scan \
  -H "Authorization: Bearer <access_token>" \
  -F "target_language=en" \
  -F "model=gpt-5.5" \
  -F "image=@/absolute/path/to/menu.png;type=image/png"
```

## JavaScript Fetch

```ts
const formData = new FormData();
formData.append("target_language", "zh-CN");
formData.append("image", file);

const response = await fetch("http://127.0.0.1:8000/api/v1/menus/scan", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${accessToken}`,
  },
  body: formData,
});

const completion = await response.json();
const menu = JSON.parse(completion.choices[0].message.content);
```

## Response

接口返回 OpenAI Chat Completions 格式。模型输出的菜单 JSON 位于 `choices[0].message.content`，内容是一个 JSON 字符串，符合后端内置的 `scan_order_menu` schema。

原始接口响应外层格式如下。为了可读性，`content` 里的完整 JSON 示例见下一段。

```json
{
  "id": "chatcmpl_xxx",
  "object": "chat.completion",
  "created": 1800000000,
  "model": "gpt-5.5",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "{\"menu\":{...},\"categories\":[...],\"items\":[...]}"
      },
      "finish_reason": "stop"
    }
  ]
}
```

`choices[0].message.content` 解析后的完整示例：

```json
{
  "menu": {
    "source_language": "ja",
    "target_language": "zh-CN",
    "currency": "JPY",
    "restaurant_name_original": "麺屋 さくら",
    "restaurant_name_translated": "樱花面屋"
  },
  "categories": [
    {
      "id": "cat_recommended",
      "parent_id": null,
      "name_original": "おすすめ",
      "name_translated": "推荐",
      "type": "recommended",
      "sort_order": 1
    },
    {
      "id": "cat_noodles",
      "parent_id": null,
      "name_original": "ラーメン",
      "name_translated": "拉面",
      "type": "noodle",
      "sort_order": 2
    },
    {
      "id": "cat_spicy_noodles",
      "parent_id": "cat_noodles",
      "name_original": "辛味ラーメン",
      "name_translated": "辣味拉面",
      "type": "series",
      "sort_order": 3
    },
    {
      "id": "cat_set_meals",
      "parent_id": null,
      "name_original": "定食",
      "name_translated": "套餐",
      "type": "set_meal",
      "sort_order": 4
    },
    {
      "id": "cat_drinks",
      "parent_id": null,
      "name_original": "ドリンク",
      "name_translated": "饮品",
      "type": "drink",
      "sort_order": 5
    },
    {
      "id": "cat_tea",
      "parent_id": "cat_drinks",
      "name_original": "お茶",
      "name_translated": "茶饮",
      "type": "tea",
      "sort_order": 6
    },
    {
      "id": "cat_desserts",
      "parent_id": null,
      "name_original": "甘味",
      "name_translated": "甜品",
      "type": "dessert",
      "sort_order": 7
    }
  ],
  "items": [
    {
      "id": "item_tori_paitan_ramen",
      "primary_category_id": "cat_noodles",
      "category_ids": ["cat_recommended", "cat_noodles"],
      "name_original": "鶏白湯ラーメン",
      "name_translated": "鸡白汤拉面",
      "description_original": "濃厚な鶏スープ、味玉付き",
      "description_translated": "浓郁鸡汤底，附溏心蛋",
      "price": {
        "amount": 980,
        "currency": "JPY",
        "raw_text": "¥980"
      },
      "item_type": "food",
      "tags": ["recommended", "signature", "popular", "hot"],
      "taste_profile": {
        "spicy_level": 0,
        "sweet_level": 1,
        "salty_level": 3,
        "sour_level": 0,
        "bitter_level": 0,
        "richness_level": 5
      },
      "allergens": ["gluten", "eggs", "soybeans"],
      "dietary": {
        "vegetarian": false,
        "vegan": false,
        "halal": null,
        "contains_pork": false,
        "contains_beef": false,
        "contains_chicken": true,
        "contains_seafood": null,
        "contains_alcohol": false
      },
      "options": [
        {
          "id": "opt_noodle_firmness",
          "name_original": "麺の硬さ",
          "name_translated": "面条硬度",
          "required": true,
          "min_select": 1,
          "max_select": 1,
          "choices": [
            {
              "id": "choice_soft",
              "name_original": "やわらかめ",
              "name_translated": "偏软",
              "extra_price": 0
            },
            {
              "id": "choice_regular",
              "name_original": "普通",
              "name_translated": "普通",
              "extra_price": 0
            },
            {
              "id": "choice_firm",
              "name_original": "かため",
              "name_translated": "偏硬",
              "extra_price": 0
            }
          ]
        },
        {
          "id": "opt_toppings",
          "name_original": "トッピング",
          "name_translated": "加料",
          "required": false,
          "min_select": 0,
          "max_select": 3,
          "choices": [
            {
              "id": "choice_extra_egg",
              "name_original": "味玉",
              "name_translated": "溏心蛋",
              "extra_price": 120
            },
            {
              "id": "choice_bamboo",
              "name_original": "メンマ",
              "name_translated": "笋干",
              "extra_price": 100
            },
            {
              "id": "choice_extra_chicken",
              "name_original": "鶏チャーシュー",
              "name_translated": "鸡叉烧",
              "extra_price": 220
            }
          ]
        }
      ],
      "availability": {
        "status": "available",
        "note": null
      },
      "confidence": {
        "ocr": 0.96,
        "translation": 0.94,
        "classification": 0.93,
        "price_detection": 0.98,
        "allergen_detection": 0.72
      }
    },
    {
      "id": "item_spicy_miso_ramen",
      "primary_category_id": "cat_spicy_noodles",
      "category_ids": ["cat_noodles", "cat_spicy_noodles"],
      "name_original": "辛味噌ラーメン",
      "name_translated": "辣味噌拉面",
      "description_original": "辛さ選べます",
      "description_translated": "可选择辣度",
      "price": {
        "amount": 1050,
        "currency": "JPY",
        "raw_text": "1,050円"
      },
      "item_type": "food",
      "tags": ["popular", "spicy", "hot"],
      "taste_profile": {
        "spicy_level": 4,
        "sweet_level": 1,
        "salty_level": 4,
        "sour_level": 1,
        "bitter_level": 0,
        "richness_level": 4
      },
      "allergens": ["gluten", "soybeans", "sesame"],
      "dietary": {
        "vegetarian": false,
        "vegan": false,
        "halal": null,
        "contains_pork": true,
        "contains_beef": false,
        "contains_chicken": true,
        "contains_seafood": null,
        "contains_alcohol": false
      },
      "options": [
        {
          "id": "opt_spice_level",
          "name_original": "辛さ",
          "name_translated": "辣度",
          "required": true,
          "min_select": 1,
          "max_select": 1,
          "choices": [
            {
              "id": "choice_spice_1",
              "name_original": "小辛",
              "name_translated": "微辣",
              "extra_price": 0
            },
            {
              "id": "choice_spice_3",
              "name_original": "中辛",
              "name_translated": "中辣",
              "extra_price": 0
            },
            {
              "id": "choice_spice_5",
              "name_original": "激辛",
              "name_translated": "特辣",
              "extra_price": 80
            }
          ]
        }
      ],
      "availability": {
        "status": "limited",
        "note": "每日限定 20 碗"
      },
      "confidence": {
        "ocr": 0.93,
        "translation": 0.91,
        "classification": 0.9,
        "price_detection": 0.97,
        "allergen_detection": 0.69
      }
    },
    {
      "id": "item_karaage_set",
      "primary_category_id": "cat_set_meals",
      "category_ids": ["cat_recommended", "cat_set_meals"],
      "name_original": "唐揚げ定食",
      "name_translated": "日式炸鸡套餐",
      "description_original": "ご飯、味噌汁、小鉢付き",
      "description_translated": "附米饭、味噌汤和小菜",
      "price": {
        "amount": 1180,
        "currency": "JPY",
        "raw_text": "¥1,180"
      },
      "item_type": "set_meal",
      "tags": ["large_portion", "hot", "kids_friendly"],
      "taste_profile": {
        "spicy_level": 0,
        "sweet_level": 1,
        "salty_level": 3,
        "sour_level": 0,
        "bitter_level": 0,
        "richness_level": 4
      },
      "allergens": ["gluten", "eggs", "soybeans"],
      "dietary": {
        "vegetarian": false,
        "vegan": false,
        "halal": null,
        "contains_pork": false,
        "contains_beef": false,
        "contains_chicken": true,
        "contains_seafood": false,
        "contains_alcohol": false
      },
      "options": [
        {
          "id": "opt_rice_size",
          "name_original": "ご飯の量",
          "name_translated": "米饭份量",
          "required": true,
          "min_select": 1,
          "max_select": 1,
          "choices": [
            {
              "id": "choice_rice_small",
              "name_original": "小盛",
              "name_translated": "小份",
              "extra_price": 0
            },
            {
              "id": "choice_rice_regular",
              "name_original": "普通",
              "name_translated": "普通",
              "extra_price": 0
            },
            {
              "id": "choice_rice_large",
              "name_original": "大盛",
              "name_translated": "大份",
              "extra_price": 100
            }
          ]
        },
        {
          "id": "opt_sauce",
          "name_original": "ソース",
          "name_translated": "酱汁",
          "required": false,
          "min_select": 0,
          "max_select": 2,
          "choices": [
            {
              "id": "choice_mayo",
              "name_original": "マヨネーズ",
              "name_translated": "蛋黄酱",
              "extra_price": 50
            },
            {
              "id": "choice_ponzu",
              "name_original": "ポン酢",
              "name_translated": "柑橘醋酱",
              "extra_price": 50
            }
          ]
        }
      ],
      "availability": {
        "status": "available",
        "note": "午餐时段供应"
      },
      "confidence": {
        "ocr": 0.95,
        "translation": 0.93,
        "classification": 0.92,
        "price_detection": 0.96,
        "allergen_detection": 0.7
      }
    },
    {
      "id": "item_matcha_latte",
      "primary_category_id": "cat_tea",
      "category_ids": ["cat_drinks", "cat_tea"],
      "name_original": "抹茶ラテ",
      "name_translated": "抹茶拿铁",
      "description_original": "アイス・ホット選択可",
      "description_translated": "可选冰饮或热饮",
      "price": {
        "amount": 560,
        "currency": "JPY",
        "raw_text": "560円"
      },
      "item_type": "drink",
      "tags": ["sweet", "iced", "hot", "vegetarian"],
      "taste_profile": {
        "spicy_level": 0,
        "sweet_level": 3,
        "salty_level": 0,
        "sour_level": 0,
        "bitter_level": 2,
        "richness_level": 3
      },
      "allergens": ["milk"],
      "dietary": {
        "vegetarian": true,
        "vegan": false,
        "halal": null,
        "contains_pork": false,
        "contains_beef": false,
        "contains_chicken": false,
        "contains_seafood": false,
        "contains_alcohol": false
      },
      "options": [
        {
          "id": "opt_temperature",
          "name_original": "温度",
          "name_translated": "温度",
          "required": true,
          "min_select": 1,
          "max_select": 1,
          "choices": [
            {
              "id": "choice_hot",
              "name_original": "ホット",
              "name_translated": "热饮",
              "extra_price": 0
            },
            {
              "id": "choice_iced",
              "name_original": "アイス",
              "name_translated": "冰饮",
              "extra_price": 0
            }
          ]
        },
        {
          "id": "opt_sweetness",
          "name_original": "甘さ",
          "name_translated": "甜度",
          "required": false,
          "min_select": 0,
          "max_select": 1,
          "choices": [
            {
              "id": "choice_less_sweet",
              "name_original": "控えめ",
              "name_translated": "少糖",
              "extra_price": 0
            },
            {
              "id": "choice_regular_sweet",
              "name_original": "普通",
              "name_translated": "正常糖",
              "extra_price": 0
            }
          ]
        }
      ],
      "availability": {
        "status": "available",
        "note": null
      },
      "confidence": {
        "ocr": 0.97,
        "translation": 0.95,
        "classification": 0.94,
        "price_detection": 0.99,
        "allergen_detection": 0.81
      }
    },
    {
      "id": "item_matcha_mochi_parfait",
      "primary_category_id": "cat_desserts",
      "category_ids": ["cat_desserts"],
      "name_original": "抹茶もちパフェ",
      "name_translated": "抹茶麻薯芭菲",
      "description_original": null,
      "description_translated": null,
      "price": {
        "amount": null,
        "currency": "JPY",
        "raw_text": "時価"
      },
      "item_type": "dessert",
      "tags": ["new", "seasonal", "sweet", "cold", "vegetarian"],
      "taste_profile": {
        "spicy_level": 0,
        "sweet_level": 4,
        "salty_level": 0,
        "sour_level": 1,
        "bitter_level": 2,
        "richness_level": 3
      },
      "allergens": ["milk", "soybeans", "unknown"],
      "dietary": {
        "vegetarian": true,
        "vegan": null,
        "halal": null,
        "contains_pork": false,
        "contains_beef": false,
        "contains_chicken": false,
        "contains_seafood": false,
        "contains_alcohol": null
      },
      "options": [],
      "availability": {
        "status": "sold_out",
        "note": "今日售罄"
      },
      "confidence": {
        "ocr": 0.84,
        "translation": 0.88,
        "classification": 0.86,
        "price_detection": 0.62,
        "allergen_detection": 0.55
      }
    }
  ]
}
```

## Errors

| 状态码 | 说明 |
| --- | --- |
| `400` | 图片为空、图片太大，或图片类型不支持。 |
| `401` | 没有登录，或没有携带有效 Bearer token。 |
| `502` | LLM 请求失败。 |
| `503` | 后端未配置 `TABERU_MATE_AI_API_KEY`。 |
