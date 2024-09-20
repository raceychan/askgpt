-- Token bucket algorithm implementation
-- Keys: [bucket_key]
-- Args: [max_tokens, refill_rate_s, token_cost]

local bucket_key, max_tokens, refill_rate_s, token_cost = KEYS[1], tonumber(ARGV[1]), tonumber(ARGV[2]),
    tonumber(ARGV[3])

-- Retrieve the current state from Redis
local bucket = redis.call('HMGET', bucket_key, 'last_refill_time', 'tokens')
local last_refill_time, tokens = tonumber(bucket[1]), tonumber(bucket[2])

-- Initialize if not present
if not last_refill_time then
    last_refill_time, tokens = redis.call('TIME')[1], max_tokens
end

-- Calculate tokens based on the elapsed time
local current_time = redis.call('TIME')[1]
local elapsed = current_time - last_refill_time
local new_tokens = math.min(max_tokens, tokens + elapsed * refill_rate_s)

-- Check if there are enough tokens
if new_tokens >= token_cost then
    local token_left = new_tokens - token_cost
    redis.call('HMSET', bucket_key, 'last_refill_time', current_time, 'tokens', token_left)
    return 0
else
    local needed = token_cost - new_tokens
    local wait_time = needed / refill_rate_s
    return wait_time
end
