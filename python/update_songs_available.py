import requests
import pandas as pd

QUERY_MAP = {}
BAD_IDS = {
    # Some packs won't let you query their data. So we just ignore these packs.
    205190, 206085, 206154, 210190, 221680, 222047, 260460, 260461, 899893, 899894,
    899895, 899900, 899901, 899902, 899903, 899904, 899905, 899906, 899907, 899908,
    899909, 899910, 1089172, 1089199, 1089222, 1089223, 1089225, 1089226, 1089227,
    1089228, 1089229, 1089230, 1089231, 1089232, 1122551, 1122552, 1122553, 1122554,
    1122555, 1122556, 1122557, 1122558, 1122559, 1122560, 1122561, 1122574, 1122575,
    1122576, 1122577, 1122578, 1122579, 258341, 222045, 222046, 222048, 222049, 206086, 206103,
}


def get_all_rocksmith_dlc():
    all_steam_apps = requests.get('https://api.steampowered.com/ISteamApps/GetAppList/v2/').json()
    df = pd.DataFrame.from_records(all_results['applist']['apps'])
    return df[df.name.str.contains('Rocksmith')]


def query_data_for_app_ids(appids):
    rows = []
    for appid in tqdm(appids):
        if appid in bad_ids:
            continue
        url = f'https://store.steampowered.com/api/appdetails/?appids={appid}&cc=us&l=english&v=1'
        if appid not in query_map:
            result = requests.get(url).json()
            if not result[str(appid)]['success']:
                print(f'Ignoring new bad id: {appid}')
                continue
            query_map[appid] = result

        data = query_map[appid][str(appid)]['data']
        date = data['release_date']['date']
        timestamp = time.mktime(datetime.strptime(date, '%b %d, %Y').timetuple()) * 1000
        name = data['name']
        rows.append((appid, name, timestamp, False))
    return pd.DataFrame.from_records(rows, columns=['appid', 'name', 'time', 'owned'])


def create_updated_song_available_csv():
    # Find all new missing DLC.
    all_dlc = get_all_rocksmith_dlc()
    prev_available_songs = pd.read_csv('songs_available_steam.csv', header=None, names=['appid', 'name', 'time', 'owned', 'unknown'])
    missing_ids = all_dlc[~all_dlc.appid.isin(available.appid)]
    
    # Clean DLC names.
    df = query_data_for_app_ids(missing_ids.appid)
    df['name'] = df.name.apply(clean)

    # Combine with old DLC.
    final_df = df[['appid', 'name', 'time', 'owned']]
    combined = pd.concat([prev_available_songs, final_df])
    combined = combined.reset_index(drop=True)
    combined['owned'] = combined.owned.astype(str).str.lower()
    
    combined.to_csv('songs_available_steam_updated.csv', header=None, index=False)


def clean_extra_rocksmith_info_from_name(s):
    transl_table = dict([
        (ord(x), ord(y))
        for x, y in zip( u"‘’´“”–-",  u"'''\"\"--")
    ])
    s = s.translate(transl_table)
    return (
        s.replace("Rocksmith® 2014 Edition – Remastered –", "")
        .replace("Rocksmith® 2014 – ", "")
        .replace("Rocksmith® 2014 Edition – Remastered -", "")
        .replace("Rocksmith® 2014 Edition - Remastered –", "")
        .replace("Rocksmith 2014 -", "")
        .replace("Rocksmith -", "")
        .replace("Rocksmith 2014 Edition - Remastered -", "")
        .replace("Rocksmith® 2014 Edition - Remastered -", "")
        .replace("Rocksmith&amp;reg; 2014 Edition &amp;ndash; Remastered &amp;ndash;", "")
        .replace("Rocksmith 2014", "")
        .replace("Rocksmith® 2014 -", "")
        .replace("Rocksmith\u00ae 2014 Edition  - Remastered \u2013", "")
        .replace("Rocksmith\u0099 - ", "")
        .replace("Rocksmith\u0099 - ", "")
        .replace("Rocksmith\u00ae 2014 Edition \u2013 Remastered \u2013", "")
        .replace("Rocksmith&amp;reg; 2014 Edition &amp;ndash; Remastered &amp;ndash;", "")
        .replace('"', "")
        .replace('\'', "")
        .strip()
    )


if __name__ == '__main__':
    create_updated_song_available_csv()
