import asyncio
import aiohttp
PROXIES = [
    "http://51.158.68.68:8811",
    "http://51.158.100.79:8811",
    "http://51.158.122.238:8811",
    "http://51.158.68.133:8811",
    "http://51.158.123.5:8811",
    "http://51.158.68.133:8811",
    "http://80.228.235.6:9898",
    "http://176.9.75.42:8080",
    "http://116.202.20.66:8080",
    "http://45.77.56.114:80",
    "http://103.149.162.195:80",
    "http://45.56.122.247:38080",
]

TEST_URL = "https://api.telegram.org"
async def test_proxy(proxy_url: str) -> bool:
    try:
        connector = aiohttp.TCPConnector()
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                TEST_URL,
                proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=8),
                ssl=False,
            ) as resp:
                if resp.status in (200, 404, 400):
                    return True
    except Exception:
        pass
    return False


async def main():
    print(">> Testing proxies for Telegram connectivity...\n")
    working = []
    for proxy in PROXIES:
        print(f"  Testing {proxy} ...", end=" ", flush=True)
        ok = await test_proxy(proxy)
        if ok:
            print("[OK] WORKS!")
            working.append(proxy)
        else:
            print("[FAIL] failed")

    print("\n" + "=" * 60)
    if working:
        print("[OK] Working proxies found! Add ONE of these to your .env:")
        for p in working:
            print(f"   HTTPS_PROXY={p}")
    else:
        print("[FAIL] No working proxies found from this list.")
        print("\nPlease try one of these options:")
        print("  1. Turn on a VPN, then run: python app.py")
        print("  2. Get a fresh proxy from https://www.socks-proxy.net/")
        print("     and add:  HTTPS_PROXY=socks5://HOST:PORT  to your .env")
        print("  3. Use your phone's hotspot and run the bot from there")


if __name__ == "__main__":
    asyncio.run(main())
