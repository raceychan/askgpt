// This file is auto-generated by @hey-api/openapi-ts

export const $Body_auth_login = {
    properties: {
        grant_type: {
            anyOf: [
                {
                    type: 'string',
                    pattern: 'password'
                },
                {
                    type: 'null'
                }
            ],
            title: 'Grant Type'
        },
        username: {
            type: 'string',
            title: 'Username'
        },
        password: {
            type: 'string',
            title: 'Password'
        },
        scope: {
            type: 'string',
            title: 'Scope',
            default: ''
        },
        client_id: {
            anyOf: [
                {
                    type: 'string'
                },
                {
                    type: 'null'
                }
            ],
            title: 'Client Id'
        },
        client_secret: {
            anyOf: [
                {
                    type: 'string'
                },
                {
                    type: 'null'
                }
            ],
            title: 'Client Secret'
        }
    },
    type: 'object',
    required: ['username', 'password'],
    title: 'Body_auth-login'
} as const;

export const $ChatCompletionRequest = {
    properties: {
        question: {
            type: 'string',
            title: 'Question'
        },
        role: {
            type: 'string',
            enum: ['system', 'user', 'assistant', 'function'],
            title: 'Role'
        },
        model: {
            type: 'string',
            enum: ['gpt-3.5-turbo', 'gpt-3.5-turbo-16k', 'gpt-4', 'gpt-4-32k', 'gpt-4-1106-preview', 'gpt-4-vision-preview'],
            title: 'Model',
            default: 'gpt-3.5-turbo'
        },
        frequency_penalty: {
            anyOf: [
                {
                    type: 'number'
                },
                {
                    type: 'null'
                }
            ],
            title: 'Frequency Penalty'
        },
        logit_bias: {
            anyOf: [
                {
                    additionalProperties: {
                        type: 'integer'
                    },
                    type: 'object'
                },
                {
                    type: 'null'
                }
            ],
            title: 'Logit Bias'
        },
        max_tokens: {
            anyOf: [
                {
                    type: 'integer'
                },
                {
                    type: 'null'
                }
            ],
            title: 'Max Tokens'
        },
        n: {
            anyOf: [
                {
                    type: 'integer'
                },
                {
                    type: 'null'
                }
            ],
            title: 'N'
        },
        presence_penalty: {
            anyOf: [
                {
                    type: 'number'
                },
                {
                    type: 'null'
                }
            ],
            title: 'Presence Penalty'
        },
        response_format: {
            title: 'Response Format'
        },
        seed: {
            anyOf: [
                {
                    type: 'integer'
                },
                {
                    type: 'null'
                }
            ],
            title: 'Seed'
        },
        stop: {
            anyOf: [
                {
                    type: 'string'
                },
                {
                    items: {
                        type: 'string'
                    },
                    type: 'array'
                },
                {
                    type: 'null'
                }
            ],
            title: 'Stop'
        },
        stream: {
            anyOf: [
                {
                    type: 'boolean'
                },
                {
                    type: 'null'
                }
            ],
            title: 'Stream'
        },
        temperature: {
            anyOf: [
                {
                    type: 'number'
                },
                {
                    type: 'null'
                }
            ],
            title: 'Temperature'
        },
        tool_choice: {
            title: 'Tool Choice'
        },
        tools: {
            anyOf: [
                {
                    items: {},
                    type: 'array'
                },
                {
                    type: 'null'
                }
            ],
            title: 'Tools'
        },
        top_p: {
            anyOf: [
                {
                    type: 'number'
                },
                {
                    type: 'null'
                }
            ],
            title: 'Top P'
        },
        user: {
            anyOf: [
                {
                    type: 'string'
                },
                {
                    type: 'null'
                }
            ],
            title: 'User'
        },
        extra_headers: {
            anyOf: [
                {
                    additionalProperties: {
                        anyOf: [
                            {
                                type: 'string'
                            },
                            {
                                const: false
                            }
                        ]
                    },
                    type: 'object'
                },
                {
                    type: 'null'
                }
            ],
            title: 'Extra Headers',
            default: {}
        },
        extra_query: {
            anyOf: [
                {
                    type: 'object'
                },
                {
                    type: 'null'
                }
            ],
            title: 'Extra Query',
            default: {}
        },
        extra_body: {
            anyOf: [
                {
                    type: 'object'
                },
                {
                    type: 'null'
                }
            ],
            title: 'Extra Body',
            default: {}
        },
        timeout: {
            anyOf: [
                {
                    type: 'number'
                },
                {
                    type: 'null'
                }
            ],
            title: 'Timeout',
            default: 120
        }
    },
    additionalProperties: false,
    type: 'object',
    required: ['question', 'role'],
    title: 'ChatCompletionRequest',
    description: `    Creates a model response for the given chat conversation.

Args:
  messages: A list of messages comprising the conversation so far.
      [Example Python code](https://cookbook.openai.com/examples/how_to_format_inputs_to_chatgpt_models).

  model: ID of the model to use. See the
      [model endpoint compatibility](https://platform.openai.com/docs/models/model-endpoint-compatibility)
      table for details on which models work with the Chat API.

  frequency_penalty: Number between -2.0 and 2.0. Positive values penalize new tokens based on their
      existing frequency in the text so far, decreasing the model's likelihood to
      repeat the same line verbatim.

      [See more information about frequency and presence penalties.](https://platform.openai.com/docs/guides/gpt/parameter-details)


  logit_bias: Modify the likelihood of specified tokens appearing in the completion.

      Accepts a JSON object that maps tokens (specified by their token ID in the
      tokenizer) to an associated bias value from -100 to 100. Mathematically, the
      bias is added to the logits generated by the model prior to sampling. The exact
      effect will vary per model, but values between -1 and 1 should decrease or
      increase likelihood of selection; values like -100 or 100 should result in a ban
      or exclusive selection of the relevant token.

  max_tokens: The maximum number of [tokens](/tokenizer) to generate in the chat completion.

      The total length of input tokens and generated tokens is limited by the model's
      context length.
      [Example Python code](https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken)
      for counting tokens.

  n: How many chat completion choices to generate for each input message.

  presence_penalty: Number between -2.0 and 2.0. Positive values penalize new tokens based on
      whether they appear in the text so far, increasing the model's likelihood to
      talk about new topics.

      [See more information about frequency and presence penalties.](https://platform.openai.com/docs/guides/gpt/parameter-details)

  response_format: An object specifying the format that the model must output. Used to enable JSON
      mode.

  seed: This feature is in Beta. If specified, our system will make a best effort to
      sample deterministically, such that repeated requests with the same \`seed\` and
      parameters should return the same result. Determinism is not guaranteed, and you
      should refer to the \`system_fingerprint\` response parameter to monitor changes
      in the backend.

  stop: Up to 4 sequences where the API will stop generating further tokens.

  stream: If set, partial message deltas will be sent, like in ChatGPT. Tokens will be
      sent as data-only
      [server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#Event_stream_format)
      as they become available, with the stream terminated by a \`data: [DONE]\`
      message.
      [Example Python code](https://cookbook.openai.com/examples/how_to_stream_completions).

  temperature: What sampling temperature to use, between 0 and 2. Higher values like 0.8 will
      make the output more random, while lower values like 0.2 will make it more
      focused and deterministic.

      We generally recommend altering this or \`top_p\` but not both.

  tool_choice: Controls which (if any) function is called by the model. \`none\` means the model
      will not call a function and instead generates a message. \`auto\` means the model
      can pick between generating a message or calling a function. Specifying a
      particular function via
      \`{"type: "function", "function": {"name": "my_function"}}\` forces the model to
      call that function.

      \`none\` is the default when no functions are present. \`auto\` is the default if
      functions are present.

  tools: A list of tools the model may call. Currently, only functions are supported as a
      tool. Use this to provide a list of functions the model may generate JSON inputs
      for.

  top_p: An alternative to sampling with temperature, called nucleus sampling, where the
      model considers the results of the tokens with top_p probability mass. So 0.1
      means only the tokens comprising the top 10% probability mass are considered.

      We generally recommend altering this or \`temperature\` but not both.

  user: A unique identifier representing your end-user, which can help OpenAI to monitor
      and detect abuse.
      [Learn more](https://platform.openai.com/docs/guides/safety-best-practices/end-user-ids).

  extra_headers: Send extra headers

  extra_query: Add additional query parameters to the request

  extra_body: Add additional JSON properties to the request

  timeout: Override the client-level default timeout for this request, in seconds`,
    examples: [
        {
            model: 'gpt-4-1106-preview',
            question: 'enter your question here',
            role: 'user',
            stream: true
        }
    ]
} as const;

export const $CreateUserRequest = {
    properties: {
        user_name: {
            type: 'string',
            title: 'User Name',
            default: ''
        },
        email: {
            type: 'string',
            format: 'email',
            title: 'Email'
        },
        password: {
            type: 'string',
            title: 'Password'
        }
    },
    additionalProperties: false,
    type: 'object',
    required: ['email', 'password'],
    title: 'CreateUserRequest'
} as const;

export const $HTTPValidationError = {
    properties: {
        detail: {
            items: {
                '$ref': '#/components/schemas/ValidationError'
            },
            type: 'array',
            title: 'Detail'
        }
    },
    type: 'object',
    title: 'HTTPValidationError'
} as const;

export const $PublicUserInfo = {
    properties: {
        user_id: {
            type: 'string',
            title: 'User Id'
        },
        user_name: {
            type: 'string',
            title: 'User Name'
        },
        email: {
            type: 'string',
            title: 'Email'
        }
    },
    type: 'object',
    required: ['user_id', 'user_name', 'email'],
    title: 'PublicUserInfo'
} as const;

export const $PulibcSessionInfo = {
    properties: {
        session_id: {
            type: 'string',
            title: 'Session Id'
        },
        session_name: {
            type: 'string',
            title: 'Session Name'
        }
    },
    type: 'object',
    required: ['session_id', 'session_name'],
    title: 'PulibcSessionInfo'
} as const;

export const $SessionRenameRequest = {
    properties: {
        name: {
            type: 'string',
            title: 'Name'
        }
    },
    additionalProperties: false,
    type: 'object',
    required: ['name'],
    title: 'SessionRenameRequest'
} as const;

export const $SupportedGPTs = {
    const: 'openai'
} as const;

export const $TokenResponse = {
    properties: {
        access_token: {
            type: 'string',
            title: 'Access Token'
        },
        token_type: {
            type: 'string',
            title: 'Token Type'
        }
    },
    type: 'object',
    required: ['access_token', 'token_type'],
    title: 'TokenResponse'
} as const;

export const $UserAddAPIRequest = {
    properties: {
        api_key: {
            type: 'string',
            title: 'Api Key'
        },
        api_type: {
            allOf: [
                {
                    '$ref': '#/components/schemas/SupportedGPTs'
                }
            ],
            default: 'openai'
        }
    },
    additionalProperties: false,
    type: 'object',
    required: ['api_key'],
    title: 'UserAddAPIRequest'
} as const;

export const $UserAuth = {
    properties: {
        user_id: {
            type: 'string',
            title: 'User Id'
        },
        role: {
            allOf: [
                {
                    '$ref': '#/components/schemas/UserRoles'
                }
            ],
            default: 'user'
        },
        credential: {
            '$ref': '#/components/schemas/UserCredential'
        },
        last_login: {
            type: 'string',
            format: 'date-time',
            title: 'Last Login'
        },
        is_active: {
            type: 'boolean',
            title: 'Is Active',
            default: true
        }
    },
    type: 'object',
    required: ['user_id', 'credential', 'last_login'],
    title: 'UserAuth'
} as const;

export const $UserCredential = {
    properties: {
        user_name: {
            type: 'string',
            title: 'User Name',
            default: ''
        },
        user_email: {
            type: 'string',
            format: 'email',
            title: 'User Email'
        },
        hash_password: {
            type: 'string',
            title: 'Hash Password'
        }
    },
    type: 'object',
    required: ['user_email', 'hash_password'],
    title: 'UserCredential'
} as const;

export const $UserRoles = {
    type: 'string',
    enum: ['admin', 'user'],
    title: 'UserRoles'
} as const;

export const $ValidationError = {
    properties: {
        loc: {
            items: {
                anyOf: [
                    {
                        type: 'string'
                    },
                    {
                        type: 'integer'
                    }
                ]
            },
            type: 'array',
            title: 'Location'
        },
        msg: {
            type: 'string',
            title: 'Message'
        },
        type: {
            type: 'string',
            title: 'Error Type'
        }
    },
    type: 'object',
    required: ['loc', 'msg', 'type'],
    title: 'ValidationError'
} as const;