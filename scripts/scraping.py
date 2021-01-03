# coding: utf-8
import pandas as pd
from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.parse import urljoin
from time import sleep
from tqdm import tqdm

# -functions- #
#@brief : urlからパースしたhtmlを取得
#@param : url(str) webサイトのurl
#@return: パースしたソース
def get_html(url):
    # url取得処理を成功するまで繰り返す
    for _ in range(10):  # 最大ループ回数
        try:
            html = urlopen(url)
            break
        except Exception as e:  # 取得失敗
            sleep(10)  # 10秒待ってからもう一度実行
    # -sourceから種族値を捜す- #
    source = BeautifulSoup(html, "html.parser")
    return source

#@brief :ポケモン個別のページから種族値・特性などを取得する
#@param :table 全ポケモンの種族値が記載されたテーブルから、１体分種族値飲みを切り出したもの
#       :url_master ポケモン個別のページへのリンク
#@return:ポケモン1体分の図鑑番号・タイプ・特性・種族が格納されたpd.series
def get_status(table, url_master):
    # status
    Number  = int(table[0].get_text())
    Name    = str(table[1].get_text())
    HP      = int(table[2].get_text())
    Attack  = int(table[3].get_text())
    Block   = int(table[4].get_text())
    Contact = int(table[5].get_text())
    Defence = int(table[6].get_text())
    Speed   = int(table[7].get_text())
    Total   = int(table[8].get_text())
    # -タイプ, 特性を取得する- #
    Type = [None, None]
    Ability = [None, None]
    HiddenAbility = None
    # ポケモン個別のページに移動
    url = urljoin(URL_MASTER, table[1].find("a").get('href'))
    source = get_html(url)
    # -タイプ取得- #
    table_type = source.find_all("div", {"class": "table layout_left"})
    # タイプのテーブルの位置を特定
    table_type = table_type[0].find("table").find_all("tr")
    index_type = [i for i, t in enumerate(table_type) if t.get_text() == "タイプ"]
    table_type = table_type[int(index_type[0])]
    # 取得
    type_all = table_type.find_all("img")
    for i, t in enumerate(type_all):
        Type[i] = str(t["alt"])
    # -特性取得- #
    table_ability = source.find_all("div", {"class": "table layout_right"})
    table_ability = table_ability[0].find("table").find_all("tr")
    # 特性、夢特性のテーブルの位置を特定
    index_ability   = [i for i, t in enumerate(table_ability) if "の特性(とくせい)" in t.get_text()]
    index_ability_H = [i for i, t in enumerate(table_ability) if "の隠れ特性(夢特性)" in t.get_text()]
    if len(index_ability) > 0:  # 特性が1つ以上あれば
        index_ability, index_ability_H = int(index_ability[0]), int(index_ability_H[0])
        # 通常特性
        num_ability = (index_ability_H - index_ability) - 1
        for i in range(num_ability):
            Ability[i] = str(table_ability[index_ability + i + 1].find("a").get_text())
        # 夢特性
        if not table_ability[index_ability_H + 1].get_text() == "なし":  # 夢特性が存在すれば
            ability_H = table_ability[index_ability_H + 1].find("a").get_text()
            HiddenAbility = str(ability_H.replace("*", ""))  # 余分な文字を削除
    # ステータスをまとめる
    Status = { "図鑑番号": Number,
               "ポケモン名": Name,
               "タイプ１": Type[0],
               "タイプ２": Type[1],
               "通常特性１": Ability[0],
               "通常特性２": Ability[1],
               "夢特性": HiddenAbility,
               "HP": HP,
               "こうげき": Attack,
               "ぼうぎょ": Block,
               "とくこう": Contact,
               "とくぼう": Defence,
               "すばやさ": Speed,
               "合計": Total}
    # return
    Status = pd.Series(Status)
    return Status

if __name__ == '__main__':
    # Variables
    URL_MASTER = "https://yakkun.com/"
    URL_LIST = "https://yakkun.com/swsh/stats_list.htm?mode=all"
    filePath_save = "/root/csv/PokemonStatus_Gen8.csv"
    # 全ポケモンの種族値が記載されているテーブルを見つける
    source_whole = get_html(URL_LIST)
    table_whole = source_whole.find_all("table", {"class": "center stupidtable stupidtable_common"})
    table = table_whole[0].find_all("tr")
    # -テーブルの処理- #
    # 最初の１匹目だけ手動
    df_StatusALL =  get_status(table[1].find_all("td"), URL_MASTER)
    for table_single in tqdm(table[2:]):
        status = get_status(table_single.find_all("td"), URL_MASTER)
        df_StatusALL = pd.concat([df_StatusALL, status], axis=1)
        print("")  # 標準出力を出すためのprint
        sleep(1)  # webサイト側の負荷を下げるためのsleep
    # Save
    df_StatusALL.T.to_csv(filePath_save, index=False, encoding="utf-8")
