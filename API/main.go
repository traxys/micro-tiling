package main

import (
	"context"
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/parnurzeal/gorequest"
	"github.com/satori/go.uuid"
	"go.etcd.io/etcd/client"
	"log"
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
	}

	return ""
}

func makePi(total int) chan int {
	ch := make(chan int)

	go func() {
		q, r, t, k, m, x := 1, 0, 1, 1, 3, 3
		count := 0

		for {
			if 4*q+r-t < m*t {
				ch <- m
				count++

				if count > total {
					break
				}

				q, r, t, k, m, x = 10*q, 10*(r-m*t), t, k, (10*(3*q+r))/t-10*m, x
			} else {
				q, r, t, k, m, x = q*k, (2*q+r)*x, t*x, k+1, (q*(7*k+2)+r*x)/(t*x), x+2
			}
		}

		close(ch)
	}()

	return ch
}

func generateAndSendSegments(kapi client.KeysAPI, jobId string) {
	ch := makePi(rand.Intn(MAX_SEGMENTS-MIN_SEGMENTS) + MIN_SEGMENTS)

	_, err := kapi.Set(context.Background(), fmt.Sprintf("/%s/state", jobId), "1", nil)
	if err != nil {
		log.Println("error writing state", err)
		return
	}

	request := gorequest.New()

	for digit := range ch {
		request.Post(os.Getenv("A_PI_ADDRESS")).
			Send(fmt.Sprintf(`{"job": "%s", "digit": "%v"}`, jobId, digit)).
			End()
	}

	request.Post(os.Getenv("A_PI_ADDRESS")).
		Send(fmt.Sprintf(`{"job": "%s", "digit": "π"}`, jobId)).
		End()
}

func main() {
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
