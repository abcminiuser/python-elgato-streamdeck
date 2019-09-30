def pulse(cycles=3,interval=0.02):
    #TODO: Make non blocking so that effect continues to cycle in parallel
    for centisecond in range(cycles * 100 * 2):
        brightness = (1 - (math.cos((centisecond / 200) *2 * math.pi))) * 100/2
        deck.set_brightness(int(brightness))
        time.sleep(interval)

def flicker(cycles=200,interval=0.1):
    #TODO: Make non blocking so that effect continues to cycle in parallel
    for cycle in range(cycles):
        deck.set_brightness(randint(0,100))
        time.sleep(randint(0,100)*interval/100)
        
def slideshow(cycles=3, interval=5):
    #TODO: Make non blocking so that effect continues to cycle in parallel
    for cycle in range(cycles):
        for source in IMAGES:
            image = create_full_deck_sized_image(deck, source)
            for k in range(deck.key_count()):
                key_image = crop_key_image_from_deck_sized_image(deck, image, k)
                deck.set_key_image(k, key_image)
            time.sleep(interval)

def shuffle(cycles=1000, interval=3):
    #TODO: Make non blocking so that effect continues to cycle in parallel
    #TODO: This runs slowly and is inefficient because images are recomputed
    # each time.  Improve using cache (e.g. @functools.lru_cache decorator)
    # or write a separate initialiser to convert images to button images once only.
    for cycle in range(cycles):
            k= randint(0,deck.key_count())
            image = create_full_deck_sized_image(deck, IMAGES[randint(0,len(IMAGES)-1)])
            key_image = crop_key_image_from_deck_sized_image(deck, image, k)
            deck.set_key_image(k, key_image)
            time.sleep(randint(0,interval))
           
