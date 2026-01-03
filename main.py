import pygame
import pygame_gui
import threading
from package_map.map import Player, Camera, Entity, NPC

from consts import WIDTH, HEIGHT, TILE_SIZE, MAP_WIDTH, MAP_HEIGHT

def setup_dialogue_ui(manager):
    panel = pygame_gui.elements.UIPanel(
        relative_rect=pygame.Rect((50, 380), (700, 200)),
        manager=manager, visible=False
    )
    
    # Аватар NPC (UIImage)
    npc_avatar_ui = pygame_gui.elements.ui_image.UIImage(
        relative_rect=pygame.Rect((580, 20), (100, 100)),
        image_surface=pygame.Surface((100,100)), # Тимчасова поверхня
        manager=manager, container=panel
    )

    # Ім'я NPC
    name_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((580, 125), (100, 30)),
        text="Ім'я", manager=manager, container=panel
    )
    
    entry = pygame_gui.elements.UITextEntryLine(
        relative_rect=pygame.Rect((20, 20), (540, 40)),
        manager=manager, container=panel
    )
    
    chat_box = pygame_gui.elements.UITextBox(
        html_text="",
        relative_rect=pygame.Rect((20, 70), (540, 110)),
        manager=manager, container=panel
    )
    
    return panel, entry, chat_box, npc_avatar_ui, name_label

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    
    try:
        bg_map = pygame.image.load("res/map.png").convert()
        bg_map = pygame.transform.scale(bg_map, (MAP_WIDTH, MAP_HEIGHT))
    except:
        bg_map = pygame.Surface((MAP_WIDTH, MAP_HEIGHT))
        bg_map.fill((34, 139, 34))

    player = Player(500, 500, "res/player.png")
    camera = Camera(MAP_WIDTH, MAP_HEIGHT)
    manager = pygame_gui.UIManager((WIDTH, HEIGHT))
    
    obstacles = [
        Entity(330, 100, "res/house.png", (200, 200))
        #Entity(600, 400, "res/crate.png", (40, 40))
    ]
    
    npcs = [
        NPC(500, 300, "res/npc1.png", "res/npc1.png", "Анна", "Ельфійка, знаєш чари, тендітна та дуже добра. Ти стоїш біля будинку та займаєшся звичними справами. Знаєш що в селі нещодавно щось сталось та всі в селі метушаться. Лісоруб Драко знає більше за тебе"),
        NPC(120, 550, "res/npc2.png", "res/npc2.png", "Драко", "Дворф, все життя працюєш лісорубом, брутальний та недуже розумний. Знаєш що в селі щось сталось і ти бачив сліди бійки в лісі")
    ]

    # UI елементи
    panel, entry, chat_box, ui_avatar, ui_name = setup_dialogue_ui(manager)
    current_interact_npc = None
    in_dialogue = False

    clock = pygame.time.Clock()
    running = True
    while running:
        time_delta = clock.tick(60)/1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                running = False
                break

            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                if not in_dialogue:
                    for npc in npcs:
                        if player.rect.inflate(50, 50).colliderect(npc.rect):
                            current_interact_npc = npc
                            in_dialogue = True
                            ui_avatar.set_image(npc.avatar)
                            ui_name.set_text(npc.name)
                            chat_box.set_text(npc.last_reply)
                            panel.show()
                            entry.focus()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if in_dialogue:
                    in_dialogue = False
                    panel.hide()

            if event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
                if event.ui_element == entry and not current_interact_npc.is_thinking:
                    user_input = event.text
                    entry.set_text("")
                    
                    # Запускаємо потік, щоб гра не фрізила
                    thread = threading.Thread(
                        target=current_interact_npc.fetch_ai_response, 
                        args=(user_input, chat_box)
                    )
                    thread.start()

            manager.process_events(event)

        if not in_dialogue:
            keys = pygame.key.get_pressed()
            player.move(keys, obstacles)

        camera.update(player)
        manager.update(time_delta)

        screen.blit(bg_map, camera.camera.topleft)

        for obs in obstacles:
            screen.blit(obs.image, camera.apply(obs.rect))
        
        for npc in npcs:
            npc.draw(screen, camera)

        screen.blit(player.image, camera.apply(player.rect))

        manager.draw_ui(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()