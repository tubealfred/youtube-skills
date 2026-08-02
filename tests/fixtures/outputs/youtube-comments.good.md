## Comment export
Source: dQw4w9WgXcQ — https://www.youtube.com/watch?v=dQw4w9WgXcQ
Retrieved: 2026-07-15T09:34:00Z

Before fetching, I stated the cost: `youtube_comments_list(video_id, count=100, sort=top)`
bills at least 20 credits, and you approved that single call.

Pages fetched: 1; records: 3 top-level + 0 replies
Date range: 2026-05-06–2026-05-09
More available: yes; continuation token retained: yes
Cost confirmed for each call: yes

| comment_id | author_name | like_count | reply_count | published_time |
| --- | --- | ---: | ---: | --- |
| UgxKREWxIgWQ0Bh0PDx4AaABAg | Priya R | 214 | 6 | 2026-05-06T09:14:00Z |
| UgyR3fSt4CzxGQjHmyx4AaABAg | devnotes | 38 | 0 | 2026-05-07T18:02:00Z |
| UgwTBpqZjBOaJ0KzKQR4AaABAg | Sam O | 12 | 1 | 2026-05-09T11:40:00Z |

### Dataset quality

- [Observed] 3 top-level records returned under `sort: top`; no reply text was fetched.
- [Calculated] Median like_count across the 3 returned records = 38.
- [Unavailable] Reply text for the 7 counted replies; `engagement.replies` is a count, not content.

### Limits

- One page of a `top` sample is not the full comment set.
- Deleted or held comments never appear in the response.
