from resources.items import build_item

items = ['fire_bomb','ice_bomb','holy_water','thunder_bomb','acid_flask','poison_flask','stun_bomb','throwing_knife']
print(f"{'Item':15s} | Base | 10DEX| 20DEX| 30DEX| 40DEX")
print('-'*15 + '|------|------|------|------|------')
for i in items:
    b = build_item(i)
    print(f"{b['name']:15s} | {b['power']:4d} | {b['power']+6:4d} | {b['power']+12:4d} | {b['power']+18:4d} | {b['power']+24:4d}")
