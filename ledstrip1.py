import pygame  # Import Pygame for graphics and game loop management.
import re  # Regular expressions for extracting RGB values.
import threading  # For running the AI chatbot in the background.
import board  # Raspberry Pi board GPIO definitions.
import neopixel  # NeoPixel library for controlling WS2812B LEDs.
import numpy as np  # NumPy for random color generation.
from time import sleep  # Sleep for LED delay.

# Importing LangChain modules for AI agent and tools
from langchain.agents import initialize_agent, Tool, AgentType  
from langchain_google_genai import ChatGoogleGenerativeAI  
from langchain_community.tools import DuckDuckGoSearchRun  

# -------------- Initialize Pygame --------------
pygame.init()

# Define screen dimensions
WIDTH, HEIGHT = 500, 400  
screen = pygame.display.set_mode((WIDTH, HEIGHT))  
pygame.display.set_caption("AI RGB Controller")  
clock = pygame.time.Clock()

running = True  
bg_color = (255, 255, 255)  # Default background color (White)

# -------------- Initialize NeoPixels --------------
LED_COUNT = 60  # Number of LEDs
np_leds = neopixel.NeoPixel(board.D18, LED_COUNT, brightness=0.5, auto_write=False)

# -------------- Initialize DuckDuckGo Search Tool --------------
search_tool = DuckDuckGoSearchRun()

# -------------- Function to Extract RGB from Text --------------
def extract_rgb_from_text(text):
    """Extracts an RGB color code from search results using regex."""
    rgb_pattern = re.search(r'(\d{1,3}),\s*(\d{1,3}),\s*(\d{1,3})', text)
    if rgb_pattern:
        return tuple(map(int, rgb_pattern.groups()))
    return None

# -------------- AI Tool: Update NeoPixel & Pygame Background --------------
def update_led_color(rgb_str):
    """
    AI tool to change NeoPixel LEDs and background based on RGB values.
    Input format: "R,G,B" (e.g., "255,100,50").
    """
    global bg_color  # Modify global background color variable

    # Convert RGB string into a tuple
    try:
        r, g, b = map(int, rgb_str.split(","))
        rgb = (r, g, b)

        # Update NeoPixels
        for i in range(LED_COUNT):
            np_leds[i] = rgb
        np_leds.show()

        # Update Pygame Background
        bg_color = rgb

        return f"Set color to RGB: {rgb}"
    
    except ValueError:
        return "Invalid RGB format. Use 'R,G,B' (e.g., '255,100,50')."

# -------------- AI Tool: Change Color by Name --------------
def change_color(color_name):
    """Changes the background color and LED color based on user input."""
    global bg_color  

    # Search for RGB values online
    print(f"Searching for RGB values for '{color_name}'...")  
    search_results = search_tool.run(f"RGB color code for {color_name}")

    # Extract RGB values from the search result
    new_rgb = extract_rgb_from_text(search_results)
    if new_rgb:
        return update_led_color(f"{new_rgb[0]},{new_rgb[1]},{new_rgb[2]}")

    return "Could not find RGB values for that color. Try another color."

# -------------- Define AI Tools --------------
color_tool = Tool(
    name="ColorChanger",
    func=change_color,
    description="Change the background color and NeoPixel LEDs by providing a color name."
)

rgb_tool = Tool(
    name="RGBController",
    func=update_led_color,
    description="Change the background color and NeoPixel LEDs by providing an RGB value in 'R,G,B' format."
)

# -------------- Initialize AI Chatbot --------------
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.5,
    max_tokens=100,
    api_key=""  # Replace with your actual API key.
)

# -------------- Initialize AI Agent with Tools --------------
agent = initialize_agent(
    tools=[color_tool, rgb_tool, search_tool],  
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# -------------- Chatbot Function (Runs in Background) --------------
def chatbot():
    """Runs an interactive chatbot in the terminal."""
    while True:
        query = input("You: ")  
        if query.lower() in ["exit", "quit"]:
            print("Goodbye!")
            pygame.quit()
            break  
        
        response = agent.invoke(query)
        print("AI:", response)

# -------------- Run Chatbot in a Separate Thread --------------
pygame_thread = threading.Thread(target=chatbot, daemon=True)  
pygame_thread.start()  

# -------------- Pygame Main Loop --------------
while running:
    screen.fill(bg_color)
    pygame.display.flip()

    for event in pygame.event.get():  
        if event.type == pygame.QUIT:
            running = False  

    clock.tick(30)  

# -------------- Quit Pygame After Loop Ends --------------
pygame.quit()
