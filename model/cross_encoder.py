from torch import nn
import torch
from transformers import AutoModelForSequenceClassification


class CrossEncoder(nn.Module):
    """
    The Cross-Encoder jointly encodes a pair of query and document into a transformer's [CLS] vector,
    which is then fed into a linear layer for calculating the relevance scores (logits).
    Attributes
    ----------
    model: result of transformers.AutoModelForSequenceClassification.from_pretrained()
        The model is composed of a linear classifier on top of the transformer's backbone.
    loss: torch.nn.CrossEntropyLoss
        Cross entropy loss for training
    """

    def __init__(self, model_name_or_dir) -> None:
        """
        Constructing Cross Encoder
        Parameters
        ----------
        model_name_or_dir: str
            name of the pretrained model which is used as an argument for
            the method AutoModelForSequenceClassification.from_pretrained
            (See: https://huggingface.co/transformers/v3.0.2/model_doc/auto.html#automodelforsequenceclassification)
        """
        super().__init__()
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name_or_dir, num_labels=1
        )
        self.loss = nn.CrossEntropyLoss()

    def score_pairs(self, pairs):
        """
        Calculating scores for a batch of (query, doc) pairs
        As the Cross-Encoder is a Sequence Classification model (i.e., it projects its last hidden states to a "classification" vector), calling the model's forward() (or __call__()) method will return the logits for the two classes (positive and negative). Hence, the score for a given query-document pair is the logit for the positive class.
        Parameters
        ----------
        pairs: dict or transformers.BatchEncoding
            the input (query, document) pairs tokenized by a HuggingFace's tokenizer. 
        Returns
        -------
        torch.Tensor: 
            a vector whose each element is the score (based on the CLS vector) of a (query, document) pair
        """
        outputs = self.model(**pairs, return_dict=True)
        logits = outputs.logits
        # scores = logits[:, 1]
        scores = logits.squeeze(-1)

        return scores

    def forward(self, pos_pairs, neg_pairs):
        """
        To train the Cross-Encoder, we can optimize the model with a (binary) cross-entropy loss. As we are using a contrastive loss, the model's predictions are the scores for both the positive pairs and the negative pairs. For a given pair of (query, positive document) and (query, negative document), the model should "choose" the positive document. This can be done by setting the target label as the one matching the index of the positive document.
        Parameters
        ----------
        pos_pairs: dict or transformers.BatchEncoding
            pairs of (query, positive document) tokenized by a HuggingFace's tokenizer.
        neg_pairs: dict or transformers.BatchEncoding
            pairs of (query, negative document) tokenized by a HuggingFace's tokenizer.
        Returns
        -------
        A tuple of (loss, pos_scores, neg_scores) which are the value of the cross entropy loss, the estimated score of
        (query, positive document) pairs and the estimated score of (query, negative document) pairs.
        The goal is to optimize for the loss
        """
        pos_scores = self.score_pairs(pos_pairs)
        neg_scores = self.score_pairs(neg_pairs)
        pos_labels = torch.ones(pos_scores.size(), device=pos_scores.device)
        neg_labels = torch.zeros(neg_scores.size(), device=neg_scores.device)
        scores = torch.cat([pos_scores, neg_scores], dim=0)
        labels = torch.cat([pos_labels, neg_labels], dim=0)
        loss = self.loss(scores, labels)

        return loss, pos_scores, neg_scores

    def save_pretrained(self, model_dir, state_dict=None):
        """
        Save the model's checkpoint to a directory
        Parameters
        ----------
        model_dir: str or Path
            path to save the model checkpoint to
        """
        self.model.save_pretrained(model_dir,)

    @classmethod
    def from_pretrained(cls, model_name_or_dir):
        """
        Load model checkpoint for a path or directory
        Parameters
        ----------
        model_name_or_dir: str
            a HuggingFace's model or path to a local checkpoint
        """
        return cls(model_name_or_dir)

