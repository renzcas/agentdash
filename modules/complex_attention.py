import torch

def build_complex_attention(attention_tensor, position_tensor=None):
    if position_tensor is None:
        seq_len = attention_tensor.shape[-1]
        position_tensor = torch.linspace(0, 2 * torch.pi, steps=seq_len)
        position_tensor = position_tensor.unsqueeze(0).repeat(attention_tensor.shape[0], 1)

    phase = torch.sin(position_tensor).unsqueeze(0).unsqueeze(0)
    phase = phase.expand_as(attention_tensor)

    A_complex = torch.complex(attention_tensor, phase)
    return A_complex

def collapse_attention(A_complex):
    return torch.abs(A_complex) ** 2

def phase_entropy(A_complex):
    phase = torch.angle(A_complex)
    entropy = -phase * torch.log(phase + 1e-9)
    return entropy.sum(dim=-1).mean(dim=0)