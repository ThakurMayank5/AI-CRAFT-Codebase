package main

import (
	"fmt"
	"log"
	"net/http"
	"os"

	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true // allow ESP32
	},
}

func wsHandler(w http.ResponseWriter, r *http.Request) {

	file, _ := os.Create("audio.raw")
	defer file.Close()

	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Println("Upgrade error:", err)
		return
	}
	defer conn.Close()

	fmt.Println("ESP32 connected")

	for {
		msgType, data, err := conn.ReadMessage()
		if err != nil {
			log.Println("Read error:", err)
			break
		}

		if msgType == websocket.BinaryMessage {
			fmt.Println("Received audio bytes:", len(data))
		}

		file.Write(data)
	}
}

func main() {
	http.HandleFunc("/", wsHandler)

	fmt.Println("WebSocket server listening on :42069")
	log.Fatal(http.ListenAndServe(":42069", nil))
}
