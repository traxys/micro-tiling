package main

import (
	"context"
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/parnurzeal/gorequest"
	"github.com/satori/go.uuid"
	log "github.com/sirupsen/logrus"
	"go.etcd.io/etcd/client"
	"math"
	"math/rand"
	"os"
	"strconv"
	"time"
)

const (
	MAX_SEGMENTS = 20
	MIN_SEGMENTS = 5
	MAX_STATE    = 42
)

var (
	Pi = []int{3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8, 9, 7, 9, 3, 2, 3, 8, 4, 6, 2, 6, 4, 3, 3, 8, 3, 2, 7, 9, 5, 0, 2, 8, 8, 4, 1, 9, 7, 1, 6, 9, 3}
)

func getPublicState(state int) string {
	if state == -1 {
		return "error"
	} else if state == 0 {
		return "started"
	} else if state <= 3 {
		return "generating segments"
	} else if state <= 7 {
		return "rotating segments"
	} else if state <= 12 {
		return "clipping segments"
	} else if state <= 19 {
		return "translating segments"
	} else if state <= 22 {
		return "cutting segments"
	} else if state == 23 {
		return "waiting fees"
	} else if state <= 31 {
		return "pruning segments"
	}

	return ""
}

func generateAndSendSegments(kapi client.KeysAPI, jobId string) {
	digits := rand.Intn(MAX_SEGMENTS-MIN_SEGMENTS) + MIN_SEGMENTS

	_, err := kapi.Set(context.Background(), fmt.Sprintf("/%s/state", jobId), "1", nil)
	if err != nil {
		log.Println("error writing state", err)
		return
	}

	request := gorequest.New()

	for i := 0; i < digits; i++ {
		log.Debug(Pi[i])
		request.Post(os.Getenv("A_PI_ADDRESS")).
			Type("multipart").
			Send(fmt.Sprintf(`{"job": "%s", "digit": "%v"}`, jobId, Pi[i])).
			End()
	}

	request.Post(os.Getenv("A_PI_ADDRESS")).
		Type("multipart").
		Send(fmt.Sprintf(`{"job": "%s", "digit": "π"}`, jobId)).
		End()
}

func main() {
	log.SetLevel(log.DebugLevel)

	cfg := client.Config{
		Endpoints: []string{os.Getenv("ETCD_ADDRESS")},
		Transport: client.DefaultTransport,
		// set timeout per request to fail fast when the target endpoint is unavailable
		HeaderTimeoutPerRequest: time.Second,
	}

	c, err := client.New(cfg)
	if err != nil {
		log.Fatal(err)
	}

	kapi := client.NewKeysAPI(c)

	r := gin.Default()

	r.GET("/", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"hello": "world",
		})
	})

	r.GET("/:jobId/state", func(c *gin.Context) {
		jobId := c.Param("jobId")

		resp, err := kapi.Get(context.Background(), fmt.Sprintf("/%s/state", jobId), nil)
		if err != nil {
			c.JSON(500, gin.H{
				"error": err,
			})
			return
		}

		state, err := strconv.Atoi(resp.Node.Value)
		if err != nil {
			c.JSON(500, gin.H{
				"error": err,
			})
			return
		}

		c.JSON(200, gin.H{
			"state":      getPublicState(state),
			"realState":  state,
			"completion": math.Round(float64(state) / MAX_STATE),
		})
	})

	r.GET("/:jobId/address", func(c *gin.Context) {
		jobId := c.Param("jobId")

		resp, err := kapi.Get(context.Background(), fmt.Sprintf("/%s/address", jobId), nil)
		if err != nil {
			c.JSON(500, gin.H{
				"error": err,
			})
			return
		}

		c.JSON(200, gin.H{
			"address": resp.Node.Value,
		})
	})

	r.GET("/:jobId/result", func(c *gin.Context) {
		jobId := c.Param("jobId")

		resp, err := kapi.Get(context.Background(), fmt.Sprintf("/%s/result", jobId), nil)
		if err != nil {
			c.JSON(500, gin.H{
				"error": err,
			})
			return
		}

		c.JSON(200, gin.H{
			"result": resp.Node.Value,
		})
	})

	r.POST("/", func(c *gin.Context) {
		jobId := uuid.NewV4().String()

		_, err := kapi.Set(context.Background(), fmt.Sprintf("/%s/state", jobId), "0", nil)
		if err != nil {
			c.JSON(500, gin.H{
				"error": err,
			})
			return
		}

		go generateAndSendSegments(kapi, jobId)

		c.JSON(200, gin.H{
			"id": jobId,
		})
	})

	r.Run()
}
