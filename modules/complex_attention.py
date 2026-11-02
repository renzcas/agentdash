import torch

def build_complex_attention(attention_tensor, position_tensor=None):
    if position_tensor is None:
        seq_len = attention_tensor.shape[-1]
        position_tensor = torch.linspace(
            0,
            2 * torch.pi,
            steps=seq_len,
            device=attention_tensor.device,
            dtype=attention_tensor.dtype,
        )

    phase = torch.sin(position_tensor).reshape(
        *((1,) * (attention_tensor.ndim - 1)), -1
    )
    phase = phase.expand_as(attention_tensor)

    A_complex = torch.complex(attention_tensor, phase)
    return A_complex

def collapse_attention(A_complex):
    return torch.abs(A_complex) ** 2

def phase_entropy(A_complex):
    phase_magnitude = torch.angle(A_complex).abs()
    epsilon = torch.finfo(phase_magnitude.dtype).eps
    probabilities = phase_magnitude / phase_magnitude.sum(
        dim=-1, keepdim=True
    ).clamp_min(epsilon)
    entropy = -probabilities * probabilities.clamp_min(epsilon).log()
    return entropy.sum(dim=-1).mean(dim=0)