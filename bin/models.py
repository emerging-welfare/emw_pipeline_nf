import torch

#### Needed for semantic classifiers ####
class MLP(torch.nn.Module): # only 1 layer
    def __init__(self, input_size, hidden_size, output_size, dropout=0.1):
        super(MLP, self).__init__()
        self.linear1 = torch.nn.Linear(input_size, hidden_size)
        self.dropout = torch.nn.Dropout(dropout) if dropout else None
        self.linear2 = torch.nn.Linear(hidden_size, output_size)
        self.act = torch.nn.GELU()

    def forward(self, x):
        x = self.act(self.linear1(x))
        if self.dropout:
            x = self.dropout(x)
        x = self.linear2(x)
        return x
####

#### Needed for multi-task model #### The original repo is in https://github.com/OsmanMutlu/ScopeIt
class Boom(torch.nn.Module):
    def __init__(self, d_model, dim_feedforward=2048, dropout=0.1):
        super(Boom, self).__init__()
        self.linear1 = torch.nn.Linear(d_model, dim_feedforward)
        self.dropout = torch.nn.Dropout(dropout) if dropout else None
        self.linear2 = torch.nn.Linear(dim_feedforward, d_model)
        self.act = torch.nn.GELU()
        self.shortcut = False
        #self.act = torch.nn.Tanh()

    def forward(self, input):
        x = self.act(self.linear1(input))
        if self.dropout: x = self.dropout(x)
        z = self.linear2(x)
        return z

class CorefHead(torch.nn.Module):
    # NOTE: Also works with batchsize
    def __init__(self, d_model, dropout=0.1, two_mlps=False):
        super(CorefHead, self).__init__()
        self.coref_mlp1 = Boom(d_model, dim_feedforward=d_model*4, dropout=dropout)
        self.two_mlps = two_mlps
        if two_mlps:
            self.coref_mlp2 = Boom(d_model, dim_feedforward=d_model*4, dropout=dropout)
        self.biaffine = BiAffine(d_model)

    def forward(self, x):
        mlp1_out = self.coref_mlp1(x) # [Sentences, HiddenSize]
        if self.two_mlps:
            mlp2_out = self.coref_mlp2(x) # [Sentences, HiddenSize]
            coref_logits = self.biaffine(mlp1_out, mlp2_out) # [Sentences, Sentences]
        else:
            coref_logits = self.biaffine(mlp1_out, mlp1_out) # [Sentences, Sentences]

        return coref_logits

class BiAffine(torch.nn.Module):
    # NOTE: Also works with batchsize
    def __init__(self, d_model):
        super(BiAffine, self).__init__()
        self.U = torch.nn.Parameter(torch.FloatTensor(d_model, d_model))
        torch.nn.init.xavier_uniform(self.U)

    def forward(self, a, b):
        out = a @ self.U @ b.transpose(-2,-1)
        return out

class ScopeIt_with_coref(torch.nn.Module):
    def __init__(self, encoder_hidden_size, hidden_size, num_layers=1, dropout=0.1,
                 num_token_labels=15, use_two_mlps_for_coref=False):
        super(ScopeIt_with_coref, self).__init__()
        self.hidden_size = hidden_size
        self.embedding_size = encoder_hidden_size
        self.bigru1 = torch.nn.GRU(self.embedding_size, hidden_size, num_layers=num_layers,
                                   bidirectional=True, batch_first=True)
        self.bigru2 = torch.nn.GRU(hidden_size, hidden_size, num_layers=num_layers,
                                   bidirectional=True, batch_first=True)

        self.token_boomer = Boom(hidden_size * 2, dim_feedforward=hidden_size*2*4,
                                 dropout=dropout)
        self.token_linear = torch.nn.Linear(self.hidden_size * 2, num_token_labels)

        self.sent_boomer = Boom(hidden_size * 2, dim_feedforward=hidden_size*2*4, dropout=dropout)
        self.sent_linear = torch.nn.Linear(self.hidden_size * 2, 1)

        self.doc_boomer = Boom(hidden_size, dim_feedforward=hidden_size*4, dropout=dropout)
        self.doc_linear = torch.nn.Linear(self.hidden_size, 1)

        # Coref
        self.coref_head = CorefHead(hidden_size*2, two_mlps=use_two_mlps_for_coref)

    def forward(self, embeddings): # embeddings ->[Sentences, SeqLen, BERT_Hidden]

        # In case we use the biGRU's output for token classification
        bigru1_all_hiddens, bigru1_last_hidden = self.bigru1(embeddings) # pass the output of bert through the first bigru to get sentence and token embeddings
        # bigru1_all_hiddens -> [Sentences, SeqLen, Hidden * 2]
        boomed_tokens = self.token_boomer(bigru1_all_hiddens) # boomed_tokens -> [Sentences, SeqLen, Hidden * 2]
        token_logits = self.token_linear(boomed_tokens) # token_logits -> [Sentences, SeqLen, num_token_labels]

        sent_embeddings = bigru1_last_hidden[0, :, :] + bigru1_last_hidden[1, :, :] # here we add the output of two GRUs (forward and backward)
        # sent_embeddings -> [Sentences, HiddenSize]

        bigru2_output = self.bigru2(sent_embeddings.unsqueeze(0))
        sent_embeddings = bigru2_output[0].squeeze(0) # [Sentences, HiddenSize*2]
        boomed_sents = self.sent_boomer(sent_embeddings)# [Sentences, HiddenSize]
        sent_logits = self.sent_linear(boomed_sents) # [Sentences, 1]
        coref_logits = self.coref_head(sent_embeddings) # [Sentences, Sentences]

        doc_embeddings = bigru2_output[1][0, 0, :] + bigru2_output[1][1, 0, :] # here we add the output of two GRUs (forward and backward)
        boomed_doc = self.doc_boomer(doc_embeddings) # [HiddenSize]
        doc_logit = self.doc_linear(boomed_doc) # [1]

        return token_logits, sent_logits, doc_logit, coref_logits
####
