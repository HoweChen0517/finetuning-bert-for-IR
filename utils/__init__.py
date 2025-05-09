from tqdm import tqdm

def write_trec_run(results, outfn, tag="neural_ir"):
    with open(outfn, "wt") as outf:
        qids = sorted(results.keys())
        for qid in tqdm(qids, desc=f"Writing run file to {outfn}"):
            rank = 1
            for docid, score in sorted(results[qid], key=lambda x: x[1], reverse=True):
                print(f"{qid} Q0 {docid} {rank} {score} {tag}", file=outf)
                rank += 1

def write_n_way_tsv(results, outfn, tag="n_way_dataset"):
    with open(outfn, "wt") as outf:
        qids = sorted(results.keys())
        for qid in tqdm(qids, desc=f"Writing run file to {outfn}"):
            rank = 1
            for did, score, label in sorted(results[qid], key=lambda x: x[1], reverse=True):
                print(f"{qid}\t{did}\t{rank}\t{score}\t{label}", file=outf)
                rank += 1