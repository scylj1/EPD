# European Patent Dataset (EPD)

**EPD** is a dataset based on patents from the European patent Office (EPO), designed to support research in claim generation and other patent-related NLP tasks. This repository contains:

- A list of **publication numbers** used for the claim generation task.
- **Code** to automatically retrieve the corresponding patent data (including claims, abstracts, descriptions, etc.) from EPO.
- More data and updates coming soon.

## Advantages 

- **Higher Quality**: EPD contains granted patents directly sourced from the EPO to ensure high-quality and legally validated data. 
- **Closer to Real-World Scenarios**: EPD includes a difficult subset designed to simulate real-world situations of claim drafting. This subset enables a more rigorous evaluation of LLMs’ ability to generate high-quality claims under practical conditions. 
- **Lower Risk of Data Leakage**: EPD consists of patents granted in 2024. This temporal gap reduces the likelihood that the data overlaps with the pre-training corpora of current LLMs.  

## Citation

If you use this dataset or code, please cite our paper:

```
@article{jiang2025enriching,
  title={Enriching Patent Claim Generation with European Patent Dataset},
  author={Jiang, Lekang and Li, Chengzu and Goetz, Stephan},
  journal={arXiv preprint arXiv:2505.12568},
  year={2025}
}
```

## License

This repository is under the Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0). Please also check the EPO's Terms and Conditions before using the data.