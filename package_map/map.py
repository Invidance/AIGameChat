
import pygame
import requests
from consts import WIDTH, HEIGHT, MAP_HEIGHT, MAP_WIDTH, STORY_BACKGROUND

class Player:
    def __init__(self, x, y, img_path):
        self.image = pygame.image.load(img_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (50, 50))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = 5

    def move(self, keys, obstacles):
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]:  dx = -self.speed
        if keys[pygame.K_RIGHT]: dx = self.speed
        if keys[pygame.K_UP]:    dy = -self.speed
        if keys[pygame.K_DOWN]:  dy = self.speed

        self.rect.x += dx
        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > MAP_WIDTH: self.rect.right = MAP_WIDTH
        
        for wall in obstacles:
            if self.rect.colliderect(wall.rect):
                if dx > 0: self.rect.right = wall.rect.left
                if dx < 0: self.rect.left = wall.rect.right

        self.rect.y += dy
        if self.rect.top < 0: self.rect.top = 0
        if self.rect.bottom > MAP_HEIGHT: self.rect.bottom = MAP_HEIGHT
        
        for wall in obstacles:
            if self.rect.colliderect(wall.rect):
                if dy > 0: self.rect.bottom = wall.rect.top
                if dy < 0: self.rect.top = wall.rect.bottom

class Entity:
    def __init__(self, x, y, img_path, size=(60, 60)):
        self.image = pygame.image.load(img_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, size)
        self.rect = self.image.get_rect(topleft=(x, y))
    
    def draw(self, screen, camera):
            screen.blit(self.image, camera.apply(self.rect))

class NPC(Entity):
    def __init__(self, x, y, img_path, avatar_path, name, personality, temp, top_p):
        super().__init__(x, y, img_path, size=(50, 50))
        self.name = name
        self.personality = personality

        self.avatar = pygame.image.load(avatar_path).convert_alpha()
        self.avatar = pygame.transform.scale(self.avatar, (100, 100))
        self.last_reply = "Привіт! Я слухаю тебе."
        self.is_thinking = False
        self.temperature = temp
        self.top_p = top_p
        self.system_promt = {"role": "system", "content": f"Ти персонаж гри в DnD. Це історія цього світу: {STORY_BACKGROUND}. Твоє ім'я {self.name}. Твій характер: {self.personality}. Відповідай коротко (1-2 речення)."}
        self.memmory = [self.system_promt]

    def draw(self, screen, camera):
        super().draw(screen, camera)

        font = pygame.font.SysFont("Arial", 16, bold=True)
        text_surf = font.render(self.name, True, (10, 10, 10))
        pos = camera.apply(self.rect)
        screen.blit(text_surf, (pos.x + (self.rect.width//2 - text_surf.get_width()//2), pos.y - 25))

    def setup_ai_parameters(self, temperature):
        self.temperature = temperature

    def fetch_ai_response(self, user_text, ui_label):
        self.is_thinking = True
        ui_label.set_text(f"<i>{self.name} думає...</i>")
        
        url = "http://localhost:1234/v1/chat/completions"
        
        self.memmory.append({"role": "user", "content": user_text})
        payload = {
            "model": "google/gemma-3n-e4b",
            "messages": self.memmory,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": 200,
            "stream": False
        }

        try:
            response = requests.post(url, json=payload, timeout=100)
            
            if response.status_code == 200:
                result = response.json()['choices'][0]['message']['content']
                self.memmory.append({"role": "assistant", "content": result})
                if self.memmory.__len__() > 10:
                    cache = self.memmory[-8:]
                    self.memmory.clear()
                    self.memmory.append(self.system_promt)
                    for v in cache:
                        self.memmory.append(v)
            else:
                result = f"Помилка сервера: {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            result = "Помилка: Сервер LM Studio не запущений!"
        except Exception as e:
            result = f"Сталася помилка: {str(e)}"

        self.last_reply = result
        ui_label.set_text(result)
        self.is_thinking = False

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)

    def apply(self, entity_rect):
        return entity_rect.move(self.camera.topleft)

    def update(self, target):
        x = -target.rect.centerx + int(WIDTH / 2)
        y = -target.rect.centery + int(HEIGHT / 2)
        x = min(0, x)
        y = min(0, y)
        x = max(-(MAP_WIDTH - WIDTH), x)
        y = max(-(MAP_HEIGHT - HEIGHT), y)
        self.camera = pygame.Rect(x, y, MAP_WIDTH, MAP_HEIGHT)